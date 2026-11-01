from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field

# --- AGENT SCHEMAS ---
class AgentBase(BaseModel):
    id: str = Field(..., json_schema_extra={"example": "agent-support-01"})
    name: str = Field(..., json_schema_extra={"example": "Customer Support Assistant"})
    role: str = Field(..., json_schema_extra={"example": "Customer Support"})
    description: Optional[str] = Field(default="", json_schema_extra={"example": "Handles order inquiries and standard refunds"})
    is_active: bool = Field(default=True)

class AgentCreate(AgentBase):
    api_key: Optional[str] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class AgentResponse(AgentBase):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- PERMISSION SCHEMAS ---
class PermissionBase(BaseModel):
    role: str
    tool_name: str
    action_type: str = "execute"
    max_amount: Optional[float] = None
    requires_approval: bool = False

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# --- POLICY EVALUATION SCHEMAS ---
class PolicyEvaluationRequest(BaseModel):
    agent_id: str
    tool_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    context: Optional[dict[str, Any]] = None

class PolicyEvaluationResponse(BaseModel):
    decision: str  # ALLOW, DENY, REQUIRE_APPROVAL
    reason: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    guardrail_flags: list[str] = Field(default_factory=list)
    approval_id: Optional[str] = None
    execution_preview: Optional[str] = None


# --- APPROVAL SCHEMAS ---
class ApprovalReviewRequest(BaseModel):
    reviewer: str = Field(..., json_schema_extra={"example": "alice_admin"})
    decision: str = Field(..., json_schema_extra={"example": "APPROVE"})  # APPROVE, REJECT
    notes: Optional[str] = Field(default="", json_schema_extra={"example": "Verified customer receipt"})

class ApprovalRequestResponse(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    agent_role: str
    tool_name: str
    parameters: dict[str, Any]
    status: str
    reason: str
    reviewer: Optional[str] = None
    reviewer_notes: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    execution_result: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- AUDIT LOG SCHEMAS ---
class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    agent_id: str
    agent_name: str
    agent_role: str
    tool_name: str
    action_type: str
    parameters: dict[str, Any]
    decision: str
    reason: str
    risk_level: str
    guardrail_flags: Optional[str] = ""
    approver: Optional[str] = None
    execution_status: str
    previous_hash: str
    current_hash: str

    model_config = ConfigDict(from_attributes=True)

class AuditVerifyResponse(BaseModel):
    is_valid: bool
    total_records: int
    message: str
    broken_at_id: Optional[int] = None


# --- MOCK AGENT SCHEMAS ---
class MockAgentRunRequest(BaseModel):
    agent_id: str
    user_prompt: str
    autonomous_execute: bool = False

class MockAgentRunResponse(BaseModel):
    agent_id: str
    agent_name: str
    agent_role: str
    user_prompt: str
    proposed_tool: str
    proposed_parameters: dict[str, Any]
    policy_decision: str
    policy_reason: str
    risk_level: str
    approval_id: Optional[str] = None
    execution_result: Optional[str] = None
