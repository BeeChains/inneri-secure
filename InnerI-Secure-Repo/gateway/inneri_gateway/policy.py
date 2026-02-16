import requests
from typing import Any, Dict
from .config import settings

def opa_decide(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    url = settings.opa_url.rstrip("/") + "/v1/data/inneri/decision"
    try:
        r = requests.post(url, json={"input": input_obj}, timeout=3)
        r.raise_for_status()
        data = r.json()
        # OPA returns {"result": {...}} under "result"
        return data.get("result", {"allow": False, "mode": "deny", "ttl_seconds": 0, "reasons": ["opa_no_result"]})
    except Exception as e:
        if settings.fail_open:
            return {"allow": True, "mode": "sandbox", "ttl_seconds": 30, "reasons": [f"opa_unavailable_fail_open:{type(e).__name__}"]}
        return {"allow": False, "mode": "deny", "ttl_seconds": 0, "reasons": [f"opa_unavailable:{type(e).__name__}"]}
