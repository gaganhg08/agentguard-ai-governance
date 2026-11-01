from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(64), primary_key=True, index=True)  # e.g. "agent-support-01"
    name = Column(String(128), nullable=False)
    role = Column(String(64), nullable=False, index=True)   # "Customer Support", "Finance", "IT Admin"
    description = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    api_key_hash = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    approval_requests = relationship("ApprovalRequest", back_populates="agent", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    name = Column(String(64), primary_key=True)
    description = Column(Text, default="")
    is_system_role = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(64), nullable=False, index=True)
    tool_name = Column(String(64), nullable=False, index=True) # Permission identifier or tool name
    description = Column(Text, default="")
    action_type = Column(String(32), default="execute")  # read, write, execute, admin
    max_amount = Column(Float, nullable=True)            # financial cap if applicable
    requires_approval = Column(Boolean, default=False)   # baseline flag


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, default="")
    target_tool = Column(String(64), nullable=False)     # specific tool name or "*"
    condition_type = Column(String(32), nullable=False)  # "amount_threshold", "role_whitelist", "guardrail_keyword"
    condition_value = Column(String(256), nullable=False)# e.g. "500", "IT Admin", "drop table"
    action = Column(String(32), nullable=False)          # "ALLOW", "DENY", "REQUIRE_APPROVAL"
    priority = Column(Integer, default=10)               # lower number = evaluated first
    is_active = Column(Boolean, default=True)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(String(64), primary_key=True, index=True)  # UUID
    agent_id = Column(String(64), ForeignKey("agents.id"), nullable=False)
    agent_name = Column(String(128), nullable=False)
    agent_role = Column(String(64), nullable=False)
    tool_name = Column(String(64), nullable=False)
    resource = Column(String(128), default="System / General")
    parameters = Column(Text, default="{}")                # JSON string
    status = Column(String(32), default="PENDING", index=True)  # PENDING, APPROVED, REJECTED
    reason = Column(Text, nullable=False)
    reviewer = Column(String(128), nullable=True)          # Human reviewer username
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime, nullable=True)
    execution_result = Column(Text, nullable=True)

    agent = relationship("Agent", back_populates="approval_requests")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    agent_id = Column(String(64), nullable=False, index=True)
    agent_name = Column(String(128), nullable=False)
    agent_role = Column(String(64), nullable=False)
    tool_name = Column(String(64), nullable=False, index=True)
    resource = Column(String(128), default="System / General", index=True)
    action_type = Column(String(32), default="execute")
    parameters = Column(Text, default="{}")
    decision = Column(String(32), nullable=False, index=True)   # ALLOW, DENY, REQUIRE_APPROVAL
    reason = Column(Text, nullable=False)
    risk_level = Column(String(16), default="LOW")              # LOW, MEDIUM, HIGH, CRITICAL
    guardrail_flags = Column(String(256), default="")
    approver = Column(String(128), nullable=True)
    execution_status = Column(String(32), default="PENDING")    # EXECUTED, BLOCKED, PENDING_APPROVAL, REJECTED
    previous_hash = Column(String(64), nullable=False)          # SHA-256 tamper-evident chain
    current_hash = Column(String(64), nullable=False)           # SHA-256
