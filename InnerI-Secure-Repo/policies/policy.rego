package inneri

# OPA input contract:
# input = {
#   "agent": {"agent_id": "...", "verification_level": "none|basic|full", "risk_tier": "low|med|high", "role": "agent_runtime|verifier|admin"},
#   "request": {"intent": "...", "tools": [{"tool_id":"echo","risk":"low"}], "data_scopes":["public"], "ip":"..."},
# }

default decision := {"allow": false, "mode": "deny", "ttl_seconds": 0, "reasons": ["default_deny"]}

# Simple RBAC/ABAC MVP:
# - deny high risk agents from calling network tools (example)
# - allow low/med risk agents to call low/med risk tools
# - sandbox unknown or medium confidence operations

decision := out {
  some t
  all_tools_low := all_tool_risk_at_most("med")
  agent_ok := input.agent.risk_tier != "high"
  scopes_ok := not contains(input.request.data_scopes, "secret")
  allow := agent_ok and all_tools_low and scopes_ok

  mode := "normal"
  ttl := 120
  reasons := []

  out := {"allow": allow, "mode": mode, "ttl_seconds": ttl, "reasons": reasons}
}

# Verifiers/admins can run more
decision := out {
  input.agent.role == "admin" or input.agent.role == "verifier"
  out := {"allow": true, "mode": "normal", "ttl_seconds": 600, "reasons": []}
}

# Sandbox if medium risk tool involved OR agent unverified
decision := out {
  not (input.agent.role == "admin" or input.agent.role == "verifier")
  not contains(input.request.data_scopes, "secret")
  (input.agent.verification_level == "none" or any_tool_risk_is("med"))
  out := {"allow": true, "mode": "sandbox", "ttl_seconds": 60, "reasons": ["sandbox_due_to_unverified_or_medium_risk"]}
}

any_tool_risk_is(level) {
  some i
  input.request.tools[i].risk == level
}

all_tool_risk_at_most(max_level) {
  not exists_tool_risk("high")
  max_level == "med"
}

exists_tool_risk(level) {
  some i
  input.request.tools[i].risk == level
}

contains(arr, x) {
  some i
  arr[i] == x
}
