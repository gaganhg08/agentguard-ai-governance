import json
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db, init_db
from backend.models import Agent, Permission
from backend.schemas import (
    AgentCreate, AgentUpdate, AgentResponse,
    PermissionCreate, PermissionResponse,
    PolicyEvaluationRequest, PolicyEvaluationResponse,
    ApprovalReviewRequest, ApprovalRequestResponse,
    AuditLogResponse, AuditVerifyResponse,
    MockAgentRunRequest, MockAgentRunResponse
)
from backend.agent_service import AgentService
from backend.policy_engine import PolicyEngine
from backend.approval_service import ApprovalService
from backend.audit_service import AuditService
from backend.mock_agent import MockAIAgent
from backend.guardrails import REGISTERED_TOOLS
from backend.seed_data import seed_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB and seed data
    init_db()
    seed_database()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AgentGuard – Enterprise-grade security and policy enforcement engine for autonomous AI agents.",
    lifespan=lifespan
)

# Enable CORS for dashboard and local clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root():
    return {
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "OPERATIONAL",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "HEALTHY"}


# -----------------------------------------------------------------------------
# AGENT MANAGEMENT ENDPOINTS
# -----------------------------------------------------------------------------
@app.get("/api/agents", response_model=list[AgentResponse], tags=["Agents"])
def list_agents(active_only: bool = False, db: Session = Depends(get_db)):
    return AgentService.list_agents(db, active_only=active_only)

@app.get("/api/agents/{agent_id}", response_model=AgentResponse, tags=["Agents"])
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = AgentService.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
    return agent

@app.post("/api/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED, tags=["Agents"])
def create_agent(agent_in: AgentCreate, db: Session = Depends(get_db)):
    try:
        return AgentService.create_agent(db, agent_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/agents/{agent_id}", response_model=AgentResponse, tags=["Agents"])
def update_agent(agent_id: str, updates: AgentUpdate, db: Session = Depends(get_db)):
    agent = AgentService.update_agent(db, agent_id, updates)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
    return agent

@app.post("/api/agents/{agent_id}/toggle", response_model=AgentResponse, tags=["Agents"])
def toggle_agent_status(agent_id: str, db: Session = Depends(get_db)):
    agent = AgentService.toggle_agent_status(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
    return agent

@app.delete("/api/agents/{agent_id}", tags=["Agents"])
def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    success = AgentService.delete_agent(db, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
    return {"message": f"Agent '{agent_id}' deleted successfully."}


# -----------------------------------------------------------------------------
# PERMISSIONS & TOOLS ENDPOINTS
# -----------------------------------------------------------------------------
@app.get("/api/tools", tags=["Tools"])
def list_registered_tools():
    return REGISTERED_TOOLS

@app.get("/api/permissions", response_model=list[PermissionResponse], tags=["Permissions"])
def list_permissions(role: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Permission)
    if role:
        query = query.filter(Permission.role == role)
    return query.all()

@app.post("/api/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED, tags=["Permissions"])
def create_permission(perm_in: PermissionCreate, db: Session = Depends(get_db)):
    perm = Permission(
        role=perm_in.role,
        tool_name=perm_in.tool_name,
        action_type=perm_in.action_type,
        max_amount=perm_in.max_amount,
        requires_approval=perm_in.requires_approval
    )
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm


# -----------------------------------------------------------------------------
# POLICY ENGINE EVALUATION
# -----------------------------------------------------------------------------
@app.post("/api/policy/evaluate", response_model=PolicyEvaluationResponse, tags=["Policy Engine"])
def evaluate_policy(request: PolicyEvaluationRequest, db: Session = Depends(get_db)):
    return PolicyEngine.evaluate(
        db=db,
        agent_id=request.agent_id,
        tool_name=request.tool_name,
        parameters=request.parameters,
        context=request.context
    )


# -----------------------------------------------------------------------------
# HUMAN APPROVAL CENTER
# -----------------------------------------------------------------------------
@app.get("/api/approvals/pending", response_model=list[ApprovalRequestResponse], tags=["Approvals"])
def get_pending_approvals(db: Session = Depends(get_db)):
    reqs = ApprovalService.get_pending_requests(db)
    results = []
    for r in reqs:
        results.append(ApprovalRequestResponse(
            id=r.id,
            agent_id=r.agent_id,
            agent_name=r.agent_name,
            agent_role=r.agent_role,
            tool_name=r.tool_name,
            parameters=json.loads(r.parameters) if r.parameters else {},
            status=r.status,
            reason=r.reason,
            reviewer=r.reviewer,
            reviewer_notes=r.reviewer_notes,
            created_at=r.created_at,
            reviewed_at=r.reviewed_at,
            execution_result=r.execution_result
        ))
    return results

@app.get("/api/approvals", response_model=list[ApprovalRequestResponse], tags=["Approvals"])
def list_all_approvals(db: Session = Depends(get_db)):
    reqs = ApprovalService.list_all_requests(db)
    results = []
    for r in reqs:
        results.append(ApprovalRequestResponse(
            id=r.id,
            agent_id=r.agent_id,
            agent_name=r.agent_name,
            agent_role=r.agent_role,
            tool_name=r.tool_name,
            parameters=json.loads(r.parameters) if r.parameters else {},
            status=r.status,
            reason=r.reason,
            reviewer=r.reviewer,
            reviewer_notes=r.reviewer_notes,
            created_at=r.created_at,
            reviewed_at=r.reviewed_at,
            execution_result=r.execution_result
        ))
    return results

@app.post("/api/approvals/{request_id}/review", response_model=ApprovalRequestResponse, tags=["Approvals"])
def review_approval(request_id: str, review_in: ApprovalReviewRequest, db: Session = Depends(get_db)):
    try:
        req = ApprovalService.review_request(
            db=db,
            request_id=request_id,
            reviewer=review_in.reviewer,
            decision=review_in.decision,
            reviewer_notes=review_in.notes
        )
        return ApprovalRequestResponse(
            id=req.id,
            agent_id=req.agent_id,
            agent_name=req.agent_name,
            agent_role=req.agent_role,
            tool_name=req.tool_name,
            parameters=json.loads(req.parameters) if req.parameters else {},
            status=req.status,
            reason=req.reason,
            reviewer=req.reviewer,
            reviewer_notes=req.reviewer_notes,
            created_at=req.created_at,
            reviewed_at=req.reviewed_at,
            execution_result=req.execution_result
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


# -----------------------------------------------------------------------------
# AUDIT LOGS & INTEGRITY VERIFICATION
# -----------------------------------------------------------------------------
@app.get("/api/audit/logs", response_model=list[AuditLogResponse], tags=["Audit"])
def get_audit_logs(
    agent_id: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    logs = AuditService.get_logs(db, agent_id=agent_id, decision=decision, limit=limit)
    results = []
    for l in logs:
        results.append(AuditLogResponse(
            id=l.id,
            timestamp=l.timestamp,
            agent_id=l.agent_id,
            agent_name=l.agent_name,
            agent_role=l.agent_role,
            tool_name=l.tool_name,
            action_type=l.action_type,
            parameters=json.loads(l.parameters) if l.parameters else {},
            decision=l.decision,
            reason=l.reason,
            risk_level=l.risk_level,
            guardrail_flags=l.guardrail_flags,
            approver=l.approver,
            execution_status=l.execution_status,
            previous_hash=l.previous_hash,
            current_hash=l.current_hash
        ))
    return results

@app.get("/api/audit/verify", response_model=AuditVerifyResponse, tags=["Audit"])
def verify_audit_integrity(db: Session = Depends(get_db)):
    res = AuditService.verify_integrity(db)
    return AuditVerifyResponse(
        is_valid=res["is_valid"],
        total_records=res["total_records"],
        message=res["message"],
        broken_at_id=res.get("broken_at_id")
    )


# -----------------------------------------------------------------------------
# MOCK AI AGENT PLAYGROUND
# -----------------------------------------------------------------------------
@app.post("/api/agent/playground/run", response_model=MockAgentRunResponse, tags=["Playground"])
def run_mock_agent(req: MockAgentRunRequest, db: Session = Depends(get_db)):
    return MockAIAgent.execute(db=db, agent_id=req.agent_id, user_prompt=req.user_prompt)
