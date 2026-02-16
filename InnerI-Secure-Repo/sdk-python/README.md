# inneri (Python SDK)

Install (editable):
```bash
pip install -e .
```

Generate an agent keypair:
```bash
python -m inneri.keys generate --out agent_ed25519.pem --pub agent_ed25519.pub.pem
```

Run example:
```bash
python examples/01_secure_call.py
```
