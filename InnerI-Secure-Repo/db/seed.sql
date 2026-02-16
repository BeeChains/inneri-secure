-- Seed a few safe tools (canonical schema mirrored from tools/*.json)
INSERT INTO tools(tool_id, name, description, risk, json_schema, requires_vault_role, enabled, version)
VALUES
('echo', 'Echo', 'Returns the provided text.', 'low',
 '{"type":"object","properties":{"text":{"type":"string","maxLength":2000}},"required":["text"],"additionalProperties":false}',
 NULL, TRUE, 1)
ON CONFLICT (tool_id) DO NOTHING;

INSERT INTO tools(tool_id, name, description, risk, json_schema, requires_vault_role, enabled, version)
VALUES
('time_now', 'Time Now', 'Returns server time (UTC).', 'low',
 '{"type":"object","properties":{},"additionalProperties":false}',
 NULL, TRUE, 1)
ON CONFLICT (tool_id) DO NOTHING;

INSERT INTO tools(tool_id, name, description, risk, json_schema, requires_vault_role, enabled, version)
VALUES
('math_eval', 'Math Eval', 'Evaluates a simple arithmetic expression.', 'med',
 '{"type":"object","properties":{"expression":{"type":"string","maxLength":200}},"required":["expression"],"additionalProperties":false}',
 NULL, TRUE, 1)
ON CONFLICT (tool_id) DO NOTHING;

-- Tool that demonstrates Vault JIT Postgres credentials (connects and returns current_user)
INSERT INTO tools(tool_id, name, description, risk, json_schema, requires_vault_role, enabled, version)
VALUES
('pg_whoami', 'PG WhoAmI', 'Uses Vault-minted Postgres creds to connect and returns current_user.', 'med',
 '{"type":"object","properties":{},"additionalProperties":false}',
 'inneri_ro', TRUE, 1)
ON CONFLICT (tool_id) DO NOTHING;

-- Demo agent + key (public key placeholder; replaced by example script)
INSERT INTO agents(agent_id, display_name, role, verification_level, risk_tier)
VALUES ('agent_demo','Demo Agent','agent_runtime','none','low')
ON CONFLICT (agent_id) DO NOTHING;

INSERT INTO reputations(agent_id, score)
VALUES ('agent_demo', 50)
ON CONFLICT (agent_id) DO NOTHING;
