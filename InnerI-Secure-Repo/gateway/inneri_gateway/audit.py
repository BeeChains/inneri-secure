from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from .models import AuditLog
from .security import canonical_json
import hashlib

def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def append_audit(db: Session, actor_agent_id: Optional[str], action: str, request_json: Dict[str, Any], result_json: Dict[str, Any]) -> Dict[str, Any]:
    prev = db.execute(select(AuditLog).order_by(desc(AuditLog.id)).limit(1)).scalar_one_or_none()
    prev_hash = prev.row_hash if prev else None

    row_obj = {
        "actor_agent_id": actor_agent_id,
        "action": action,
        "request": request_json,
        "result": result_json,
        "prev_hash": prev_hash,
    }
    row_hash = _sha256_hex(canonical_json(row_obj))

    rec = AuditLog(
        actor_agent_id=actor_agent_id,
        action=action,
        request_json=request_json,
        result_json=result_json,
        prev_hash=prev_hash,
        row_hash=row_hash,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"audit_id": rec.id, "row_hash": row_hash, "prev_hash": prev_hash}
