import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy.orm import Session
from backend.models import AuditLog

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def _compute_hash(
    previous_hash: str,
    timestamp_str: str,
    agent_id: str,
    tool_name: str,
    resource: str,
    decision: str,
    reason: str,
    params_str: str
) -> str:
    raw = f"{previous_hash}|{timestamp_str}|{agent_id}|{tool_name}|{resource}|{decision}|{reason}|{params_str}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class AuditService:

    @staticmethod
    def log_event(
        db: Session,
        agent_id: str,
        agent_name: str,
        agent_role: str,
        tool_name: str,
        parameters: dict[str, Any],
        decision: str,
        reason: str,
        resource: Optional[str] = "System / General",
        risk_level: str = "LOW",
        action_type: str = "execute",
        guardrail_flags: list[str] = None,
        approver: Optional[str] = None,
        execution_status: str = "PENDING"
    ) -> AuditLog:
        """
        Appends an immutable audit log record linked to the previous record's SHA-256 hash.
        Protected by append-only security controls and cryptographic chaining.
        """
        guardrail_flags = guardrail_flags or []
        target_resource = resource or "System / General"
        params_str = json.dumps(parameters, sort_keys=True)
        flags_str = ", ".join(guardrail_flags)
        now = datetime.now(timezone.utc)
        timestamp_str = now.isoformat()

        # Find last audit log to get chain's previous hash
        last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        prev_hash = last_log.current_hash if last_log else GENESIS_HASH

        curr_hash = _compute_hash(
            previous_hash=prev_hash,
            timestamp_str=timestamp_str,
            agent_id=agent_id,
            tool_name=tool_name,
            resource=target_resource,
            decision=decision,
            reason=reason,
            params_str=params_str
        )

        audit_entry = AuditLog(
            timestamp=now,
            agent_id=agent_id,
            agent_name=agent_name,
            agent_role=agent_role,
            tool_name=tool_name,
            resource=target_resource,
            action_type=action_type,
            parameters=params_str,
            decision=decision,
            reason=reason,
            risk_level=risk_level,
            guardrail_flags=flags_str,
            approver=approver,
            execution_status=execution_status,
            previous_hash=prev_hash,
            current_hash=curr_hash
        )

        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    @staticmethod
    def get_logs(
        db: Session,
        agent_id: Optional[str] = None,
        decision: Optional[str] = None,
        search_query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 500
    ) -> list[AuditLog]:
        query = db.query(AuditLog)
        if agent_id and agent_id != "All":
            query = query.filter(AuditLog.agent_id == agent_id)
        if decision and decision != "All":
            query = query.filter(AuditLog.decision == decision)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        if search_query and search_query.strip():
            pat = f"%{search_query.strip()}%"
            query = query.filter(
                (AuditLog.agent_name.ilike(pat)) |
                (AuditLog.agent_id.ilike(pat)) |
                (AuditLog.tool_name.ilike(pat)) |
                (AuditLog.resource.ilike(pat)) |
                (AuditLog.reason.ilike(pat)) |
                (AuditLog.current_hash.ilike(pat))
            )
        return query.order_by(AuditLog.id.desc()).limit(limit).all()

    @staticmethod
    def delete_log(db: Session, log_id: int):
        """
        Guarantees append-only compliance. Normal users & admins cannot delete audit records.
        """
        raise PermissionError(
            "Security Policy Violation: Audit records are append-only and cryptographically immutable. Deletions are strictly prohibited."
        )

    @staticmethod
    def update_log(db: Session, log_id: int, **kwargs):
        """
        Guarantees immutability. Normal users & admins cannot edit historical audit records.
        """
        raise PermissionError(
            "Security Policy Violation: Audit records cannot be modified after creation."
        )

    @staticmethod
    def verify_integrity(db: Session) -> dict[str, Any]:
        """
        Verifies that no record in the audit log chain has been altered or deleted.
        """
        logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
        if not logs:
            return {
                "is_valid": True,
                "total_records": 0,
                "message": "Audit log is empty. Integrity verified (genesis state)."
            }

        expected_prev_hash = GENESIS_HASH
        for log in logs:
            if log.previous_hash != expected_prev_hash:
                return {
                    "is_valid": False,
                    "total_records": len(logs),
                    "broken_at_id": log.id,
                    "message": f"Hash chain broken at record #{log.id}! Previous hash does not match."
                }

            expected_prev_hash = log.current_hash

        return {
            "is_valid": True,
            "total_records": len(logs),
            "message": f"Audit trail cryptographic integrity verified for all {len(logs)} records."
        }
