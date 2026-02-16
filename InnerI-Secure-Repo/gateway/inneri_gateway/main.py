from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from jsonschema import validate, ValidationError
from typing import Any, Dict, Optional
import time

from .db import get_db
from .models import Agent, AgentKey, Tool, Reputation, Verification
from .schemas import (
    AgentRegisterRequest, AgentNonceResponse, AgentAuthRequest,
    SecureCallRequest, VerifyAgentRequest
)
from .security import generate_nonce, now_unix, verify_agent_signature, sign_receipt, canonical_json
from .jwt_auth import issue_jwt, require_auth
from .secrets_vault import VaultClient
from .policy import opa_decide
from .tools_runtime import run_tool
from .audit import append_audit
from .config import settings

app = FastAPI(title="Inner I Gateway", version="0.1.0")

# In-memory nonce store for MVP; replace with Redis in prod
_NONCES: Dict[str, Dict[str, Any]] = {}

def _get_agent(db: Session, agent_id: str) -> Agent:
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent_not_found")
    return agent

def _get_agent_key(db: Session, agent_id: str) -> AgentKey:
    k = db.get(AgentKey, agent_id)
    if not k:
        raise HTTPException(status_code=404, detail="agent_key_not_found")
    return k

@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "inneri-gateway", "version": app.version}

@app.post("/v1/agents/register")
def register_agent(req: AgentRegisterRequest, db: Session = Depends(get_db)):
    if db.get(Agent, req.agent_id):
        raise HTTPException(status_code=409, detail="agent_id_taken")

    agent = Agent(agent_id=req.agent_id, display_name=req.display_name)
    db.add(agent)
    db.add(AgentKey(agent_id=req.agent_id, public_key_ed25519=req.public_key_ed25519_pem))
    db.add(Reputation(agent_id=req.agent_id, score=50))
    db.commit()
    append_audit(db, req.agent_id, "agent.register", req.model_dump(), {"ok": True})
    return {"ok": True, "agent_id": req.agent_id}

@app.get("/v1/agents/{agent_id}/nonce", response_model=AgentNonceResponse)
def get_nonce(agent_id: str, db: Session = Depends(get_db)):
    _get_agent(db, agent_id)
    nonce = generate_nonce()
    exp = now_unix() + 120
    _NONCES[agent_id] = {"nonce": nonce, "exp": exp}
    return AgentNonceResponse(agent_id=agent_id, nonce=nonce, expires_unix=exp)

@app.post("/v1/agents/auth")
def agent_auth(req: AgentAuthRequest, db: Session = Depends(get_db)):
    agent = _get_agent(db, req.agent_id)
    key = _get_agent_key(db, req.agent_id)
    entry = _NONCES.get(req.agent_id)
    if not entry or entry["nonce"] != req.nonce or entry["exp"] < now_unix():
        raise HTTPException(status_code=401, detail="invalid_or_expired_nonce")

    message = canonical_json({"agent_id": req.agent_id, "nonce": req.nonce}).encode("utf-8")
    if not verify_agent_signature(key.public_key_ed25519, message, req.signature_b64url):
        raise HTTPException(status_code=401, detail="bad_signature")

    # Issue short-lived JWT (portable identity) for subsequent calls.
    jwt_token = issue_jwt({
        "sub": req.agent_id,
        "agent_id": req.agent_id,
        "role": agent.role,
        "verification_level": agent.verification_level,
        "risk_tier": agent.risk_tier,
    }, ttl_seconds=180)
    append_audit(db, req.agent_id, "agent.auth", req.model_dump(), {"ok": True})
    return {"ok": True, "access_token": jwt_token, "token_type": "Bearer", "ttl_seconds": 180, "agent": {
        "agent_id": agent.agent_id,
        "role": agent.role,
        "verification_level": agent.verification_level,
        "risk_tier": agent.risk_tier
    }}

@app.get("/v1/tools")
def list_tools(db: Session = Depends(get_db)):
    tools = db.execute(select(Tool).where(Tool.enabled == True)).scalars().all()
    return {"tools": [{"tool_id": t.tool_id, "name": t.name, "description": t.description, "risk": t.risk, "version": t.version} for t in tools]}

def _tool_meta(db: Session, tool_id: str) -> Tool:
    t = db.get(Tool, tool_id)
    if not t or not t.enabled:
        raise HTTPException(status_code=404, detail="tool_not_found_or_disabled")
    return t

@app.post("/v1/secure_call")
def secure_call(req: SecureCallRequest, db: Session = Depends(get_db), token_claims: dict = Depends(require_auth)):
    agent = _get_agent(db, req.agent_id)

    # AuthZ: agent can only act as itself unless admin/verifier
    if token_claims.get("agent_id") != req.agent_id and token_claims.get("role") not in ("admin", "verifier"):
        raise HTTPException(status_code=403, detail="token_agent_mismatch")

    # Build OPA input
    tools_meta = []
    for tc in req.tools:
        t = _tool_meta(db, tc.tool_id)
        tools_meta.append({"tool_id": t.tool_id, "risk": t.risk})

    decision = opa_decide({
        "agent": {
            "agent_id": agent.agent_id,
            "verification_level": agent.verification_level,
            "risk_tier": agent.risk_tier,
            "role": agent.role
        },
        "request": {
            "intent": req.intent,
            "tools": tools_meta,
            "data_scopes": req.data_scopes,
        }
    })

    if not decision.get("allow", False):
        append_audit(db, req.agent_id, "secure_call.deny", req.model_dump(), {"decision": decision})
        raise HTTPException(status_code=403, detail={"denied": True, "decision": decision})

    mode = decision.get("mode", "normal")

    outputs = []
    for tc in req.tools:
        tool = _tool_meta(db, tc.tool_id)
        # Schema validation blocks many injection paths
        try:
            validate(instance=tc.args, schema=tool.json_schema)
        except ValidationError as e:
            append_audit(db, req.agent_id, "tool.args_invalid", {"tool_id": tool.tool_id, "args": tc.args}, {"error": str(e)})
            raise HTTPException(status_code=422, detail={"tool_id": tool.tool_id, "error": "args_schema_invalid", "message": str(e)})

        # Sandbox: block medium/high risk tools (example)
        if mode == "sandbox" and tool.risk != "low":
            outputs.append({"tool_id": tool.tool_id, "blocked": True, "reason": "sandbox_mode"})
            continue

        try:
            # Tool execution
            if tool.tool_id == "pg_whoami":
                # Demonstrates Vault JIT Postgres credentials
                if not tool.requires_vault_role:
                    raise Exception("pg_whoami missing requires_vault_role")
                vc = VaultClient()
                creds = vc.get_postgres_creds(tool.requires_vault_role)
                u = creds["data"]["username"]
                p = creds["data"]["password"]
                # Connect to Postgres using minted creds
                import psycopg
                dsn = "dbname=inneri host=postgres port=5432 user=%s password=%s" % (u, p)
                with psycopg.connect(dsn) as conn:
                    with conn.cursor() as cur:
                        cur.execute("select current_user")
                        user = cur.fetchone()[0]
                out = {"current_user": user, "lease_id": creds.get("lease_id"), "lease_duration": creds.get("lease_duration")}
            else:
                out = run_tool(tool.tool_id, tc.args)
            outputs.append({"tool_id": tool.tool_id, "output": out})
        except Exception as e:
            outputs.append({"tool_id": tool.tool_id, "error": str(e)})

    # Update reputation (simple heuristic)
    rep = db.get(Reputation, req.agent_id)
    if rep:
        delta = 1 if mode == "normal" else 0
        rep.score = max(0, min(100, rep.score + delta))
        db.add(rep)
        db.commit()

    receipt = {
        "ts_unix": int(time.time()),
        "agent_id": req.agent_id,
        "intent": req.intent,
        "mode": mode,
        "decision": decision,
        "outputs_hash": hashlib_sha256(canonical_json(outputs)),
    }
    receipt["signature"] = sign_receipt(receipt, settings.receipt_signing_key)

    audit = append_audit(db, req.agent_id, "secure_call.run", req.model_dump(), {"mode": mode, "decision": decision, "outputs": outputs, "receipt": receipt})

    return {"outputs": outputs, "receipt": receipt, "audit": audit}

def hashlib_sha256(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

@app.post("/v1/verify/agent")
def verify_agent(req: VerifyAgentRequest, db: Session = Depends(get_db), token_claims: dict = Depends(require_auth)):
    agent = _get_agent(db, req.agent_id)

    # AuthZ: agent can only act as itself unless admin/verifier
    if token_claims.get("agent_id") != req.agent_id and token_claims.get("role") not in ("admin", "verifier"):
        raise HTTPException(status_code=403, detail="token_agent_mismatch")

    # MVP verification: basic checks + report
    rep = db.get(Reputation, req.agent_id)
    report = {
        "agent_id": agent.agent_id,
        "display_name": agent.display_name,
        "role": agent.role,
        "verification_level_before": agent.verification_level,
        "risk_tier": agent.risk_tier,
        "reputation_score": rep.score if rep else None,
        "checks": {
            "has_key": db.get(AgentKey, req.agent_id) is not None,
            "has_reputation": rep is not None,
        },
        "notes": req.notes
    }

    level = req.level
    if level not in ("basic", "technical", "performance", "continuous"):
        raise HTTPException(status_code=400, detail="invalid_verification_level")

    # Upgrade agent verification_level for demo
    agent.verification_level = "basic" if level == "basic" else "full"
    db.add(agent)
    v = Verification(agent_id=req.agent_id, level=level, report=report)
    db.add(v)
    db.commit()

    receipt = {"agent_id": req.agent_id, "level": level, "ts_unix": int(time.time())}
    receipt["signature"] = sign_receipt(receipt, settings.receipt_signing_key)

    append_audit(db, req.agent_id, "agent.verify", req.model_dump(), {"report": report, "receipt": receipt})
    return {"ok": True, "report": report, "receipt": receipt}

@app.get("/v1/reputation/{agent_id}")
def get_reputation(agent_id: str, db: Session = Depends(get_db), token_claims: dict = Depends(require_auth)):
    _get_agent(db, agent_id)
    rep = db.get(Reputation, agent_id)
    return {"agent_id": agent_id, "score": rep.score if rep else 0}
