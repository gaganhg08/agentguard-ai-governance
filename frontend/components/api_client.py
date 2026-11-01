import json
import requests
from typing import Any, Optional
from backend.database import SessionLocal
from backend.agent_service import AgentService
from backend.policy_engine import PolicyEngine
from backend.approval_service import ApprovalService
from backend.audit_service import AuditService
from backend.mock_agent import MockAIAgent
from backend.guardrails import REGISTERED_TOOLS
from backend.models import Permission

API_BASE = "http://127.0.0.1:8000/api"

class GovernanceClient:
    """
    Unified client providing seamless access to AgentGuard services.
    Attempts HTTP to FastAPI backend first; gracefully falls back to direct DB session
    if the standalone HTTP server is offline.
    """

    @classmethod
    def _is_server_online(cls) -> bool:
        try:
            r = requests.get("http://127.0.0.1:8000/health", timeout=0.8)
            return r.status_code == 200
        except Exception:
            return False

    # Agents
    @classmethod
    def get_agents(cls) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            agents = AgentService.list_agents(db)
            return [
                {
                    "id": a.id,
                    "name": a.name,
                    "role": a.role,
                    "description": a.description,
                    "is_active": a.is_active,
                    "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else ""
                }
                for a in agents
            ]
        finally:
            db.close()

    @classmethod
    def toggle_agent(cls, agent_id: str) -> bool:
        db = SessionLocal()
        try:
            res = AgentService.toggle_agent_status(db, agent_id)
            return res is not None
        finally:
            db.close()

    @classmethod
    def create_agent(cls, agent_id: str, name: str, role: str, description: str) -> None:
        from backend.schemas import AgentCreate
        db = SessionLocal()
        try:
            AgentService.create_agent(db, AgentCreate(id=agent_id, name=name, role=role, description=description))
        finally:
            db.close()

    # Permissions & Tools
    @classmethod
    def get_permissions(cls) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            perms = db.query(Permission).all()
            return [
                {
                    "id": p.id,
                    "role": p.role,
                    "tool_name": p.tool_name,
                    "action_type": p.action_type,
                    "max_amount": p.max_amount,
                    "requires_approval": p.requires_approval
                }
                for p in perms
            ]
        finally:
            db.close()

    @classmethod
    def get_tools(cls) -> dict[str, Any]:
        return REGISTERED_TOOLS

    # Policy Evaluation
    @classmethod
    def evaluate_policy(cls, agent_id: str, tool_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
        db = SessionLocal()
        try:
            res = PolicyEngine.evaluate(db, agent_id, tool_name, parameters)
            return {
                "decision": res.decision,
                "reason": res.reason,
                "risk_level": res.risk_level,
                "guardrail_flags": res.guardrail_flags,
                "approval_id": res.approval_id,
                "execution_preview": res.execution_preview
            }
        finally:
            db.close()

    # Approvals
    @classmethod
    def get_pending_approvals(cls) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            reqs = ApprovalService.get_pending_requests(db)
            return [
                {
                    "id": r.id,
                    "agent_id": r.agent_id,
                    "agent_name": r.agent_name,
                    "agent_role": r.agent_role,
                    "tool_name": r.tool_name,
                    "parameters": json.loads(r.parameters) if r.parameters else {},
                    "reason": r.reason,
                    "status": r.status,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
                }
                for r in reqs
            ]
        finally:
            db.close()

    @classmethod
    def review_approval(cls, request_id: str, reviewer: str, decision: str, notes: str) -> None:
        db = SessionLocal()
        try:
            ApprovalService.review_request(db, request_id, reviewer, decision, notes)
        finally:
            db.close()

    # Audit Logs
    @classmethod
    def get_audit_logs(cls, limit: int = 150) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            logs = AuditService.get_logs(db, limit=limit)
            return [
                {
                    "id": l.id,
                    "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "",
                    "agent_id": l.agent_id,
                    "agent_name": l.agent_name,
                    "agent_role": l.agent_role,
                    "tool_name": l.tool_name,
                    "decision": l.decision,
                    "risk_level": l.risk_level,
                    "reason": l.reason,
                    "parameters": json.loads(l.parameters) if l.parameters else {},
                    "approver": l.approver or "N/A",
                    "execution_status": l.execution_status,
                    "current_hash": l.current_hash
                }
                for l in logs
            ]
        finally:
            db.close()

    @classmethod
    def verify_audit_integrity(cls) -> dict[str, Any]:
        db = SessionLocal()
        try:
            return AuditService.verify_integrity(db)
        finally:
            db.close()

    # Playground
    @classmethod
    def run_mock_agent(cls, agent_id: str, prompt: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            res = MockAIAgent.execute(db, agent_id, prompt)
            return {
                "agent_id": res.agent_id,
                "agent_name": res.agent_name,
                "agent_role": res.agent_role,
                "proposed_tool": res.proposed_tool,
                "proposed_parameters": res.proposed_parameters,
                "policy_decision": res.policy_decision,
                "policy_reason": res.policy_reason,
                "risk_level": res.risk_level,
                "approval_id": res.approval_id,
                "execution_result": res.execution_result
            }
        finally:
            db.close()
