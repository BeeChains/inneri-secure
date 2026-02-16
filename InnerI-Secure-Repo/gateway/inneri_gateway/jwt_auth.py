from typing import Dict, Any, Optional
import time
import jwt  # PyJWT
from fastapi import Header, HTTPException, Depends
from .config import settings

def issue_jwt(claims: Dict[str, Any], ttl_seconds: int = 180) -> str:
    now = int(time.time())
    payload = {
        **claims,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    return jwt.encode(payload, settings.jwt_signing_key, algorithm="HS256")

def decode_jwt(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_signing_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="jwt_expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="jwt_invalid")

def require_auth(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing_bearer_token")
    token = authorization.split(" ", 1)[1].strip()
    return decode_jwt(token)
