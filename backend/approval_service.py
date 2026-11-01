import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy.orm import Session
from backend.models import ApprovalRequest, Agent
from backend.audit_service import AuditService

class ApprovalService:

    @staticmethod
    def create_request(
        db: Session,
        agent_id: str,
        agent_name: str,
        agent_role: str,
        tool_name: str,
        parameters: dict[str, Any],
        reason: str
    ) -> ApprovalRequest:
        req_id = f"appr-{uuid.uuid4().hex[:8]}"
        req = ApprovalRequest(
            id=req_id,
            agent_id=agent_id,
            agent_name=agent_name,
            agent_role=agent_role,
            tool_name=tool_name,
            parameters=json.dumps(parameters),
            status="PENDING",
            reason=reason,
            created_at=datetime.now(timezone.utc)
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def get_pending_requests(db: Session) -> list[ApprovalRequest]:
        return db.query(ApprovalRequest).filter(ApprovalRequest.status == "PENDING").order_by(ApprovalRequest.created_at.desc()).all()

    @staticmethod
    def get_request(db: Session, request_id: str) -> Optional[ApprovalRequest]:
        return db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()

    @staticmethod
    def list_all_requests(db: Session) -> list[ApprovalRequest]:
        return db.query(ApprovalRequest).order_by(ApprovalRequest.created_at.desc()).all()

    @staticmethod
    def review_request(
        db: Session,
        request_id: str,
        reviewer: str,
        decision: str,  # "APPROVE" or "REJECT"
        reviewer_notes: Optional[str] = ""
    ) -> ApprovalRequest:
        req = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
        if not req:
            raise ValueError(f"Approval request '{request_id}' not found.")

        if req.status != "PENDING":
            raise ValueError(f"Approval request '{request_id}' is already {req.status}.")

        # CRITICAL SECURITY RULE: Agent cannot approve its own request
        cleaned_reviewer = reviewer.strip().lower()
        if cleaned_reviewer in [req.agent_id.lower(), req.agent_name.lower(), "agent", "self"]:
            raise PermissionError(
                f"Security Violation: Agent '{req.agent_id}' cannot approve its own action! Human reviewer required."
            )

        if not reviewer or cleaned_reviewer == "":
            raise ValueError("Reviewer identity cannot be empty.")

        req.reviewed_at = datetime.now(timezone.utc)
        req.reviewer = reviewer.strip()
        req.reviewer_notes = reviewer_notes or ""

        parsed_params = json.loads(req.parameters) if req.parameters else {}

        if decision.upper() == "APPROVE":
            req.status = "APPROVED"
            execution_msg = f"Action '{req.tool_name}' executed successfully under authorization from {req.reviewer}."
            req.execution_result = json.dumps({"status": "SUCCESS", "message": execution_msg})

            # Record in append-only audit trail
            AuditService.log_event(
                db=db,
                agent_id=req.agent_id,
                agent_name=req.agent_name,
                agent_role=req.agent_role,
                tool_name=req.tool_name,
                parameters=parsed_params,
                decision="ALLOW",
                reason=f"Approved by human reviewer '{req.reviewer}'. Note: {req.reviewer_notes}",
                risk_level="HIGH",
                approver=req.reviewer,
                execution_status="EXECUTED"
            )
        else:
            req.status = "REJECTED"
            rejection_msg = f"Action '{req.tool_name}' rejected by {req.reviewer}. Reason: {req.reviewer_notes}"
            req.execution_result = json.dumps({"status": "REJECTED", "message": rejection_msg})

            AuditService.log_event(
                db=db,
                agent_id=req.agent_id,
                agent_name=req.agent_name,
                agent_role=req.agent_role,
                tool_name=req.tool_name,
                parameters=parsed_params,
                decision="DENY",
                reason=f"Rejected by human reviewer '{req.reviewer}'. Note: {req.reviewer_notes}",
                risk_level="HIGH",
                approver=req.reviewer,
                execution_status="REJECTED"
            )

        db.commit()
        db.refresh(req)
        return req
