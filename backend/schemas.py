from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field

# --- AGENT SCHEMAS ---
class AgentBase(BaseModel):
    id: str = Field(
        ...,
        min_length=3,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        json_schema_extra={"example": "agent-support-01"}
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=128,
        json_schema_extra={"example": "Customer Support Assistant"}
    )
    role: str = Field(..., json_schema_extra={"example": "Customer Support"})
    description: Optional[str] = Field(default="", json_schema_extra={"example": "Handles order inquiries and standard refunds"})
    is_active: bool = Field(default=True)

class AgentCreate(AgentBase):
    api_key: Optional[str] = Field(default=None, description="Optional agent authentication credential, stored as salted hash")

class AgentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=128)
    role: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class AgentResponse(AgentBase):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AgentDetailResponse(AgentResponse):
    total_evaluations: int = 0
    allowed_actions: int = 0
    blocked_actions: int = 0
    pending_approvals: int = 0
    last_active: Optional[datetime] = None
    allowed_tools: list[str] = Field(default_factory=list)

class AgentActivityItem(BaseModel):
    id: int
    timestamp: datetime
    tool_name: str
    decision: str
    risk_level: str
    reason: str
    execution_status: str

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
    tool_name: Optional[str] = None
    action: Optional[str] = None  # Alias for tool_name
    resource: Optional[str] = None # e.g. "order:ORD-1092", "server:prod-ingress"
    parameters: dict[str, Any] = Field(default_factory=dict)
    context: Optional[dict[str, Any]] = None

class PolicyEvaluationResponse(BaseModel):
    decision: str  # ALLOW, DENY, REQUIRE_APPROVAL
    agent_id: str = ""
    agent_name: str = ""
    agent_role: str = ""
    requested_action: str = ""
    target_resource: Optional[str] = "Global / General"
    applicable_policy: str = "Default-Deny Policy"
    reason: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    requires_human_approval: bool = False
    guardrail_flags: list[str] = Field(default_factory=list)
    approval_id: Optional[str] = None
    execution_preview: Optional[str] = None
    evaluation_trace: list[dict[str, str]] = Field(default_factory=list)


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
    resource: Optional[str] = "System / General"
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
    resource: Optional[str] = "System / General"
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
    target_resource: Optional[str] = "System / General"
    proposed_parameters: dict[str, Any]
    policy_decision: str
    policy_reason: str
    applicable_policy: Optional[str] = "Default-Deny Policy"
    risk_level: str
    approval_id: Optional[str] = None
    execution_result: Optional[str] = None
    guardrail_flags: list[str] = Field(default_factory=list)
    evaluation_trace: list[dict[str, str]] = Field(default_factory=list)
