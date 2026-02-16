# Security Policy (MVP)

This repository is an **MVP** intended for local development and early prototyping.

## Do not use in production without hardening
- Vault is running in **dev mode** in `docker-compose.yml`.
- The Vault root token is **static** for local use.
- JWT signing key is a **shared secret** in env.
- Nonce storage is **in-memory** (should be Redis).
- Receipt signing uses **HMAC** (upgrade to Ed25519/PKI).

## Recommended production hardening checklist
1. Vault HA + KMS auto-unseal + disable dev mode
2. Gateway authenticates to Vault via **AppRole** or Kubernetes auth (no root token)
3. Use **mTLS** service-to-service + (optional) SPIFFE/SPIRE identities
4. Replace in-memory nonce store with Redis and add rate limits
5. Move policies into versioned OPA bundles (Git-backed)
6. Use Ed25519 signing for receipts + rotate keys
7. Add dedicated tool runner sandbox (gVisor/Firecracker) for untrusted execution
