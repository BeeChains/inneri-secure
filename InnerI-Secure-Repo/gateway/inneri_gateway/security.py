import base64, json, time, hmac, hashlib
from typing import Any, Dict
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def b64url_decode(s: str) -> bytes:
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s.encode("utf-8"))

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

def sign_receipt(receipt: Dict[str, Any], signing_key: str) -> str:
    # HMAC for MVP; replace with Ed25519/PKI in v1
    mac = hmac.new(signing_key.encode("utf-8"), canonical_json(receipt).encode("utf-8"), hashlib.sha256).digest()
    return b64url(mac)

def verify_agent_signature(public_key_pem: str, message: bytes, signature_b64: str) -> bool:
    try:
        pub = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        if not isinstance(pub, Ed25519PublicKey):
            return False
        sig = b64url_decode(signature_b64)
        pub.verify(sig, message)
        return True
    except Exception:
        return False

def generate_nonce() -> str:
    import os
    return b64url(os.urandom(24))

def now_unix() -> int:
    return int(time.time())
