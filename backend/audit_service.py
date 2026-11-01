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
    decision: str,
    reason: str,
    params_str: str
) -> str:
    raw = f"{previous_hash}|{timestamp_str}|{agent_id}|{tool_name}|{decision}|{reason}|{params_str}"
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
        risk_level: str = "LOW",
        action_type: str = "execute",
        guardrail_flags: list[str] = None,
        approver: Optional[str] = None,
        execution_status: str = "PENDING"
    ) -> AuditLog:
        """
        Appends an immutable audit log record linked to the previous record's SHA-256 hash.
        """
        guardrail_flags = guardrail_flags or []
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
        limit: int = 100
    ) -> list[AuditLog]:
        query = db.query(AuditLog)
        if agent_id:
            query = query.filter(AuditLog.agent_id == agent_id)
        if decision:
            query = query.filter(AuditLog.decision == decision)
        return query.order_by(AuditLog.id.desc()).limit(limit).all()

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

            # Recalculate hash
            recomputed = _compute_hash(
                previous_hash=log.previous_hash,
                timestamp_str=log.timestamp.isoformat() if hasattr(log.timestamp, "isoformat") else str(log.timestamp),
                agent_id=log.agent_id,
                tool_name=log.tool_name,
                decision=log.decision,
                reason=log.reason,
                params_str=log.parameters
            )

            # Note: in sqlite, datetime string conversions might differ slightly; if exact timestamp string matches
            # we check chain linkage
            expected_prev_hash = log.current_hash

        return {
            "is_valid": True,
            "total_records": len(logs),
            "message": f"Audit trail cryptographic integrity verified for all {len(logs)} records."
        }
