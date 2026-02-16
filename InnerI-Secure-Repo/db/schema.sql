-- Inner I MVP schema (Postgres 16)
-- NOTE: keep it simple; add migrations later.

CREATE TABLE IF NOT EXISTS agents (
  agent_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'agent_runtime',
  verification_level TEXT NOT NULL DEFAULT 'none',
  risk_tier TEXT NOT NULL DEFAULT 'low',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_keys (
  agent_id TEXT PRIMARY KEY REFERENCES agents(agent_id) ON DELETE CASCADE,
  public_key_ed25519 TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tools (
  tool_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  risk TEXT NOT NULL DEFAULT 'low', -- low|med|high
  json_schema JSONB NOT NULL,
  requires_vault_role TEXT,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- append-only audit log with hash chain
CREATE TABLE IF NOT EXISTS audit_log (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor_agent_id TEXT,
  action TEXT NOT NULL,
  request_json JSONB NOT NULL,
  result_json JSONB NOT NULL,
  prev_hash TEXT,
  row_hash TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor_agent_id);

CREATE TABLE IF NOT EXISTS reputations (
  agent_id TEXT PRIMARY KEY REFERENCES agents(agent_id) ON DELETE CASCADE,
  score INTEGER NOT NULL DEFAULT 50,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS verifications (
  id BIGSERIAL PRIMARY KEY,
  agent_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  level TEXT NOT NULL, -- basic|technical|performance|continuous
  report JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
