from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Text, Boolean, Integer, BigInteger, DateTime, JSON, func, ForeignKey

class Base(DeclarativeBase):
    pass

class Agent(Base):
    __tablename__ = "agents"
    agent_id: Mapped[str] = mapped_column(Text, primary_key=True)
    display_name: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text, default="agent_runtime")
    verification_level: Mapped[str] = mapped_column(Text, default="none")
    risk_tier: Mapped[str] = mapped_column(Text, default="low")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class AgentKey(Base):
    __tablename__ = "agent_keys"
    agent_id: Mapped[str] = mapped_column(Text, ForeignKey("agents.agent_id", ondelete="CASCADE"), primary_key=True)
    public_key_ed25519: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Tool(Base):
    __tablename__ = "tools"
    tool_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    risk: Mapped[str] = mapped_column(Text, default="low")
    json_schema: Mapped[dict] = mapped_column(JSON)
    requires_vault_role: Mapped[str] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ts: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actor_agent_id: Mapped[str] = mapped_column(Text, nullable=True)
    action: Mapped[str] = mapped_column(Text)
    request_json: Mapped[dict] = mapped_column(JSON)
    result_json: Mapped[dict] = mapped_column(JSON)
    prev_hash: Mapped[str] = mapped_column(Text, nullable=True)
    row_hash: Mapped[str] = mapped_column(Text)

class Reputation(Base):
    __tablename__ = "reputations"
    agent_id: Mapped[str] = mapped_column(Text, ForeignKey("agents.agent_id", ondelete="CASCADE"), primary_key=True)
    score: Mapped[int] = mapped_column(Integer, default=50)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Verification(Base):
    __tablename__ = "verifications"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    agent_id: Mapped[str] = mapped_column(Text, ForeignKey("agents.agent_id", ondelete="CASCADE"))
    level: Mapped[str] = mapped_column(Text)
    report: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
