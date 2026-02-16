import json
import requests
from typing import Any, Dict, List, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import base64

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

class InnerIClient:
    def __init__(self, gateway_url: str):
        self.gateway_url = gateway_url.rstrip("/")

    def register_agent(self, agent_id: str, display_name: str, public_key_pem: str) -> Dict[str, Any]:
        r = requests.post(f"{self.gateway_url}/v1/agents/register", json={
            "agent_id": agent_id,
            "display_name": display_name,
            "public_key_ed25519_pem": public_key_pem,
        }, timeout=10)
        r.raise_for_status()
        return r.json()

    def get_nonce(self, agent_id: str) -> Dict[str, Any]:
        r = requests.get(f"{self.gateway_url}/v1/agents/{agent_id}/nonce", timeout=10)
        r.raise_for_status()
        return r.json()

    def auth(self, agent_id: str, priv: Ed25519PrivateKey) -> Dict[str, Any]:
        n = self.get_nonce(agent_id)
        msg = _canonical_json({"agent_id": agent_id, "nonce": n["nonce"]}).encode("utf-8")
        sig = priv.sign(msg)
        payload = {"agent_id": agent_id, "nonce": n["nonce"], "signature_b64url": _b64url(sig)}
        r = requests.post(f"{self.gateway_url}/v1/agents/auth", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()

    def secure_call(self, agent_id: str, intent: str, tools: List[Dict[str, Any]], data_scopes: List[str], bearer_token: str, model: Optional[str]=None, prompt: Optional[str]=None) -> Dict[str, Any]:
        body = {
            "agent_id": agent_id,
            "intent": intent,
            "model": model,
            "prompt": prompt,
            "tools": tools,
            "data_scopes": data_scopes,
        }
        r = requests.post(f"{self.gateway_url}/v1/secure_call", json=body, timeout=30, headers={"Authorization": f"Bearer {bearer_token}"})
        r.raise_for_status()
        return r.json()

def _load_priv(path: str) -> Ed25519PrivateKey:
    with open(path, "rb") as f:
        data = f.read()
    key = serialization.load_pem_private_key(data, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("Not an Ed25519 private key")
    return key

def _load_pub_pem(path: str) -> str:
    with open(path, "rb") as f:
        return f.read().decode("utf-8")

def secure_agent_call(
    gateway_url: str,
    agent_private_key_path: str,
    agent_id: str,
    intent: str,
    tools: List[Dict[str, Any]],
    data_scopes: Optional[List[str]] = None,
    model: Optional[str] = None,
    prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """One-liner call that authenticates + runs tools through Inner I."""
    data_scopes = data_scopes or ["public"]
    client = InnerIClient(gateway_url=gateway_url)
    priv = _load_priv(agent_private_key_path)
    # auth handshake (nonce + signature)
    auth = client.auth(agent_id, priv)
    token = auth.get("access_token")
    if not token:
        raise RuntimeError("Gateway did not return access_token")
    return client.secure_call(agent_id=agent_id, intent=intent, tools=tools, data_scopes=data_scopes, bearer_token=token, model=model, prompt=prompt)
