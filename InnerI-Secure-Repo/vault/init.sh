#!/bin/sh
set -eu

# This script runs inside the Vault container (dev mode already up).
# It enables the database secrets engine and configures dynamic Postgres creds.

echo "[vault] Enabling database secrets engine..."
vault secrets enable -path=database database >/dev/null 2>&1 || true

echo "[vault] Configuring Postgres connection..."
vault write database/config/inneri \
  plugin_name=postgresql-database-plugin \
  allowed_roles="inneri_ro" \
  connection_url="postgresql://{{username}}:{{password}}@postgres:5432/inneri?sslmode=disable" \
  username="inneri" \
  password="inneri" >/dev/null

# Create a role that Vault will mint dynamically.
# For MVP we grant minimal privileges; adjust for your schema later.
echo "[vault] Creating dynamic credential role inneri_ro..."
vault write database/roles/inneri_ro \
  db_name=inneri \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT CONNECT ON DATABASE inneri TO \"{{name}}\"; GRANT USAGE ON SCHEMA public TO \"{{name}}\";" \
  default_ttl="60s" \
  max_ttl="300s" >/dev/null

echo "[vault] OK: database/creds/inneri_ro ready."
