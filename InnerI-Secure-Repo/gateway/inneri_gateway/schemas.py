from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class AgentRegisterRequest(BaseModel):
    agent_id: str = Field(min_length=3, max_length=64)
    display_name: str = Field(min_length=1, max_length=128)
    public_key_ed25519_pem: str = Field(min_length=32)

class AgentNonceResponse(BaseModel):
    agent_id: str
    nonce: str
    expires_unix: int

class AgentAuthRequest(BaseModel):
    agent_id: str
    nonce: str
    signature_b64url: str

class ToolCall(BaseModel):
    tool_id: str
    args: Dict[str, Any] = Field(default_factory=dict)

class SecureCallRequest(BaseModel):
    agent_id: str
    intent: str
    model: Optional[str] = None
    prompt: Optional[str] = None
    tools: List[ToolCall] = Field(default_factory=list)
    data_scopes: List[str] = Field(default_factory=lambda: ["public"])

class VerifyAgentRequest(BaseModel):
    agent_id: str
    level: str = Field(default="basic")  # basic|technical|performance|continuous
    notes: Optional[str] = None
