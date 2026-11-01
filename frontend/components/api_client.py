import json
from typing import Any, Optional
from backend.database import SessionLocal
from backend.agent_service import AgentService
from backend.policy_engine import PolicyEngine
from backend.approval_service import ApprovalService
from backend.audit_service import AuditService
from backend.mock_agent import MockAIAgent
from backend.guardrails import REGISTERED_TOOLS
from backend.models import Permission, PolicyRule, Agent
from backend.config import settings

class GovernanceClient:
    """
    Enterprise Data & Service Gateway for AgentGuard UI.
    Uses direct database transactions with ACID compliance.
    """

    # --- AGENT FLEET ---
    @classmethod
    def get_agents(
        cls,
        active_only: bool = False,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            agents = AgentService.list_agents(db, active_only=active_only, search=search, role=role, is_active=is_active)
            return [
                {
                    "id": a.id,
                    "name": a.name,
                    "role": a.role,
                    "description": a.description,
                    "is_active": a.is_active,
                    "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else "",
                    "updated_at": a.updated_at.strftime("%Y-%m-%d %H:%M:%S") if a.updated_at else ""
                }
                for a in agents
            ]
        finally:
            db.close()

    @classmethod
    def get_agent_detail(cls, agent_id: str) -> Optional[dict[str, Any]]:
        db = SessionLocal()
        try:
            detail = AgentService.get_agent_detail(db, agent_id)
            if not detail:
                return None
            detail["created_at_fmt"] = detail["created_at"].strftime("%Y-%m-%d %H:%M:%S") if detail["created_at"] else "—"
            detail["updated_at_fmt"] = detail["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if detail["updated_at"] else "—"
            detail["last_active_fmt"] = detail["last_active"].strftime("%Y-%m-%d %H:%M:%S") if detail["last_active"] else "Never"
            return detail
        finally:
            db.close()

    @classmethod
    def get_agent_activity(cls, agent_id: str, limit: int = 50) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            logs = AgentService.get_agent_activity(db, agent_id, limit=limit)
            return [
                {
                    "id": l.id,
                    "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "—",
                    "tool_name": l.tool_name,
                    "decision": l.decision,
                    "risk_level": l.risk_level,
                    "reason": l.reason,
                    "execution_status": l.execution_status
                }
                for l in logs
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
    def create_agent(
        cls,
        agent_id: str,
        name: str,
        role: str,
        description: str,
        is_active: bool = True,
        api_key: Optional[str] = None
    ) -> None:
        from backend.schemas import AgentCreate
        db = SessionLocal()
        try:
            AgentService.create_agent(
                db,
                AgentCreate(
                    id=agent_id,
                    name=name,
                    role=role,
                    description=description,
                    is_active=is_active,
                    api_key=api_key
                )
            )
        finally:
            db.close()

    @classmethod
    def update_agent(
        cls,
        agent_id: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        from backend.schemas import AgentUpdate
        db = SessionLocal()
        try:
            res = AgentService.update_agent(
                db,
                agent_id,
                AgentUpdate(
                    name=name,
                    role=role,
                    description=description,
                    is_active=is_active
                )
            )
            return res is not None
        finally:
            db.close()

    @classmethod
    def delete_agent(cls, agent_id: str) -> bool:
        db = SessionLocal()
        try:
            return AgentService.delete_agent(db, agent_id)
        finally:
            db.close()

    # --- SECURITY POLICIES ---
    @classmethod
    def get_policies(cls) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            rules = db.query(PolicyRule).order_by(PolicyRule.priority.asc()).all()
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "target_tool": r.target_tool,
                    "condition_type": r.condition_type,
                    "condition_value": r.condition_value,
                    "action": r.action,
                    "priority": r.priority,
                    "is_active": r.is_active
                }
                for r in rules
            ]
        finally:
            db.close()

    @classmethod
    def create_policy(cls, name: str, description: str, target_tool: str, condition_type: str, condition_value: str, action: str, priority: int) -> None:
        db = SessionLocal()
        try:
            new_rule = PolicyRule(
                name=name,
                description=description,
                target_tool=target_tool,
                condition_type=condition_type,
                condition_value=condition_value,
                action=action,
                priority=priority,
                is_active=True
            )
            db.add(new_rule)
            db.commit()
        finally:
            db.close()

    @classmethod
    def toggle_policy(cls, rule_id: int) -> None:
        db = SessionLocal()
        try:
            rule = db.query(PolicyRule).filter(PolicyRule.id == rule_id).first()
            if rule:
                rule.is_active = not rule.is_active
                db.commit()
        finally:
            db.close()

    # --- PERMISSIONS & ROLES (RBAC) ---
    @classmethod
    def get_roles(cls) -> list[dict[str, Any]]:
        from backend.rbac_service import RBACService
        db = SessionLocal()
        try:
            return RBACService.list_roles(db)
        finally:
            db.close()

    @classmethod
    def create_role(cls, name: str, description: str, authorized_by: str = "security_lead") -> None:
        from backend.rbac_service import RBACService
        db = SessionLocal()
        try:
            RBACService.create_role(db, name, description, authorized_by)
        finally:
            db.close()

    @classmethod
    def assign_role_to_agent(cls, agent_id: str, new_role: str, authorized_by: str = "security_lead") -> None:
        from backend.rbac_service import RBACService
        db = SessionLocal()
        try:
            RBACService.assign_role_to_agent(db, agent_id, new_role, authorized_by)
        finally:
            db.close()

    @classmethod
    def get_permissions(cls, role: Optional[str] = None) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            query = db.query(Permission)
            if role and role != "All":
                query = query.filter(Permission.role == role)
            perms = query.all()
            return [
                {
                    "id": p.id,
                    "role": p.role,
                    "tool_name": p.tool_name,
                    "description": p.description or "",
                    "action_type": p.action_type,
                    "max_amount": p.max_amount if p.max_amount else "Unlimited",
                    "requires_approval": p.requires_approval
                }
                for p in perms
            ]
        finally:
            db.close()

    @classmethod
    def grant_permission(
        cls,
        role: str,
        tool_name: str,
        action_type: str = "execute",
        max_amount: Optional[float] = None,
        requires_approval: bool = False,
        description: str = "",
        authorized_by: str = "security_lead"
    ) -> None:
        from backend.rbac_service import RBACService
        db = SessionLocal()
        try:
            RBACService.grant_permission(
                db=db,
                role=role,
                tool_name=tool_name,
                action_type=action_type,
                max_amount=max_amount,
                requires_approval=requires_approval,
                description=description,
                authorized_by=authorized_by
            )
        finally:
            db.close()

    @classmethod
    def revoke_permission(cls, permission_id: int, authorized_by: str = "security_lead") -> bool:
        from backend.rbac_service import RBACService
        db = SessionLocal()
        try:
            return RBACService.revoke_permission(db, permission_id, authorized_by)
        finally:
            db.close()

    @classmethod
    def get_permission_matrix(cls) -> dict[str, Any]:
        from backend.rbac_service import RBACService
        db = SessionLocal()
        try:
            return RBACService.get_permission_matrix(db)
        finally:
            db.close()

    @classmethod
    def delete_policy(cls, rule_id: int) -> bool:
        db = SessionLocal()
        try:
            rule = db.query(PolicyRule).filter(PolicyRule.id == rule_id).first()
            if not rule:
                return False
            db.delete(rule)
            db.commit()
            return True
        finally:
            db.close()

    @classmethod
    def get_tools(cls) -> dict[str, Any]:
        return REGISTERED_TOOLS

    # --- GUARDRAILS CONFIG ---
    @classmethod
    def get_guardrail_config(cls) -> dict[str, Any]:
        return {
            "injection_keywords": settings.INJECTION_KEYWORDS,
            "sensitive_tools": list(settings.SENSITIVE_TOOLS),
            "refund_threshold": settings.REFUND_APPROVAL_THRESHOLD,
            "payment_threshold": settings.PAYMENT_APPROVAL_THRESHOLD,
            "sql_filter_enabled": True,
            "shell_filter_enabled": True,
            "default_deny": True
        }

    # --- POLICY EVALUATION ---
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

    # --- APPROVAL CENTER ---
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
    def get_all_approvals(cls) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            reqs = ApprovalService.list_all_requests(db)
            return [
                {
                    "id": r.id,
                    "agent_id": r.agent_id,
                    "agent_name": r.agent_name,
                    "tool_name": r.tool_name,
                    "parameters": json.loads(r.parameters) if r.parameters else {},
                    "status": r.status,
                    "reason": r.reason,
                    "reviewer": r.reviewer or "—",
                    "reviewed_at": r.reviewed_at.strftime("%Y-%m-%d %H:%M:%S") if r.reviewed_at else "—",
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

    # --- AUDIT TRAIL ---
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
                    "previous_hash": l.previous_hash,
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

    # --- AI PLAYGROUND ---
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
