import os
import requests
import inneri
from cryptography.hazmat.primitives import serialization

GATEWAY = os.getenv("INNERI_GATEWAY_URL", "http://localhost:8080")
AGENT_ID = os.getenv("INNERI_AGENT_ID", "agent_demo")

PRIV = "./agent_ed25519.pem"
PUB = "./agent_ed25519.pub.pem"

def ensure_keys():
    if not os.path.exists(PRIV) or not os.path.exists(PUB):
        # generate via module
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "inneri", "keys", "generate", "--out", PRIV, "--pub", PUB])

def ensure_agent_registered():
    # Try register; ignore if exists
    pub_pem = open(PUB, "r", encoding="utf-8").read()
    try:
        requests.post(f"{GATEWAY}/v1/agents/register", json={
            "agent_id": AGENT_ID,
            "display_name": "Demo Agent (SDK)",
            "public_key_ed25519_pem": pub_pem
        }, timeout=10).raise_for_status()
        print("Registered agent:", AGENT_ID)
    except Exception:
        print("Agent already registered (or gateway not ready).")

def main():
    ensure_keys()
    ensure_agent_registered()

    res = inneri.secure_agent_call(
        gateway_url=GATEWAY,
        agent_private_key_path=PRIV,
        agent_id=AGENT_ID,
        intent="demo_tools",
        tools=[
            {"tool_id": "echo", "args": {"text": "hello from Inner I secure_agent_call"}},
            {"tool_id": "time_now", "args": {}},
            {"tool_id": "math_eval", "args": {"expression": "2*(7+3)"}} ,
            {"tool_id": "pg_whoami", "args": {}}
        ],
        data_scopes=["public"]
    )
    print("\nOutputs:", res["outputs"])
    print("\nReceipt:", res["receipt"])
    print("\nAudit:", res["audit"])

if __name__ == "__main__":
    main()
