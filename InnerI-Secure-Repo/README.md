# Inner I — Zero‑Trust Agent Gateway (GitHub Starter Repo)

This repo is a **working MVP** of the Inner I architecture:
- **Invariant Observer Gateway** for agents/tools/models
- **Zero‑trust**: authenticate every call, policy every call, audit every call
- **Vetted tool registry** + JSON schema arg validation
- **OPA policy engine** (RBAC/ABAC + sandboxing)
- **Signed execution receipts** (tamper‑evident audit chain)
- **Python SDK** with a single entry point: `inneri.secure_agent_call()`

> Ship this first. Then evolve Vault/JIT secrets, continuous verification, and marketplace API.

---

## Quickstart (Docker)

### 1) Start stack
```bash
docker compose up --build
```

Services:
- `gateway` (FastAPI) : http://localhost:8080
- `opa` : http://localhost:8181
- `postgres` : localhost:5432
- `vault` (dev) : http://localhost:8200 (token: `inneri-root`)

### 2) Seed tools (already happens on first boot)
Tools are stored in Postgres table `tools`.

### 3) Run SDK example
```bash
cd sdk-python
python -m venv .venv && source .venv/bin/activate
pip install -e .
python examples/01_secure_call.py
```

---

## SDK: `inneri.secure_agent_call()`

```python
import inneri

result = inneri.secure_agent_call(
    gateway_url="http://localhost:8080",
    agent_private_key_path="./agent_ed25519.pem",
    agent_id="agent_demo",
    intent="demo_echo",
    model=None,
    prompt=None,
    tools=[{"tool_id": "echo", "args": {"text": "hello from Inner I"}}],
    data_scopes=["public"],
)
print(result["outputs"])
print(result["receipt"]["signature"])
```

---

## Repo layout

- `gateway/` FastAPI gateway + audit + OPA integration
- `sdk-python/` Python package `inneri` + examples
- `policies/` OPA Rego policies + bundle config
- `tools/` tool schemas (canonical source)
- `db/` Postgres schema + seed SQL
- `.github/workflows/` CI

---

## Security notes (MVP)

This is a **starter**:
- Vault/JIT credentials are **wired** (dev Vault) for dynamic Postgres creds (tool `pg_whoami`).
- Prompt injection defense is implemented as **tool-call gating + schema validation + deny-by-default**.
- OPA is **fail-closed** by default (set `INNERI_FAIL_OPEN=true` to fail-open during dev).

---

## Next upgrades (recommended)
1. Replace stub secrets with **HashiCorp Vault** dynamic creds.
2. Add **mTLS** service identity (SPIFFE/SPIRE).
3. Continuous verification + drift monitoring.
4. API-first “verification badge” + marketplace integration.

---

## License
MIT


---

## What you upload to GitHub
Upload **the entire repo** exactly as-is (root files + folders).

Suggested repo name:
- `inneri-secure` or `inneri-gateway-secure`

After unzipping:
```bash
cd inneri-secure
git init
git add .
git commit -m "Initial commit: Inner I secure gateway (Vault + JWT MVP)"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

---

## Vault + JWT (how it works)
- **JWT**: short-lived portable identity for API calls (SDK uses Bearer token).
- **Vault**: issues short-lived *dynamic* Postgres credentials for tools that need secrets.
- **OPA**: evaluates allow/deny/sandbox decisions for each request.

The demo tool `pg_whoami` proves Vault JIT creds are working by returning `current_user`
from Postgres using a Vault-minted username/password lease.

---

## Troubleshooting
### Gateway can't talk to Vault
- Confirm Vault is up: http://localhost:8200
- Dev token is: `inneri-root`
- In Docker, gateway uses `INNERI_VAULT_ADDR=http://vault:8200` (compose service name)

### OPA denies everything
- OPA is fail-closed by default.
- For local dev only: set `INNERI_FAIL_OPEN=true` in `docker-compose.yml`.

### `pg_whoami` fails with permissions
This MVP grants minimal DB permissions in `vault/init.sh`. If you need SELECT privileges on
tables, extend the role creation statements accordingly.

---

## License
MIT
