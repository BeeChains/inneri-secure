import requests
from typing import Dict, Any
from .config import settings

class VaultClient:
    def __init__(self, addr: str | None = None, token: str | None = None):
        self.addr = (addr or settings.vault_addr).rstrip("/")
        self.token = token or settings.vault_token
        if not self.token:
            raise RuntimeError("Vault token not set (INNERI_VAULT_TOKEN)")

    def get_postgres_creds(self, role: str) -> Dict[str, Any]:
        # Vault: GET /v1/database/creds/<role>
        url = f"{self.addr}/v1/database/creds/{role}"
        r = requests.get(url, headers={"X-Vault-Token": self.token}, timeout=5)
        r.raise_for_status()
        data = r.json()
        # { "request_id":..., "lease_id":..., "lease_duration":..., "renewable":..., "data": {"username":..,"password":..} }
        return data
