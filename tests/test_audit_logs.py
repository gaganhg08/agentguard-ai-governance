import pytest
from backend.audit_service import AuditService
from backend.models import AuditLog

def test_audit_log_append_and_chain(db_session):
    # Log two distinct events
    entry1 = AuditService.log_event(
        db=db_session,
        agent_id="agent-support-01",
        agent_name="Frontline Support",
        agent_role="Customer Support",
        tool_name="view_order",
        parameters={"order_id": "ORD-123"},
        decision="ALLOW",
        reason="Routine customer lookup"
    )
    assert entry1.id is not None
    assert entry1.current_hash is not None

    entry2 = AuditService.log_event(
        db=db_session,
        agent_id="agent-support-01",
        agent_name="Frontline Support",
        agent_role="Customer Support",
        tool_name="issue_refund",
        parameters={"order_id": "ORD-123", "amount": 25.0},
        decision="ALLOW",
        reason="Approved refund"
    )
    # Check cryptographic link
    assert entry2.previous_hash == entry1.current_hash

def test_audit_integrity_verification(db_session):
    # Verify chain integrity
    res = AuditService.verify_integrity(db_session)
    assert res["is_valid"] is True
    assert res["total_records"] >= 1

def test_tamper_detection(db_session):
    # Intentionally corrupt a hash in the database to simulate tampering
    log = db_session.query(AuditLog).first()
    original_prev_hash = log.previous_hash
    log.previous_hash = "corrupted_hash_tamper_detected_1234567890"
    db_session.commit()

    # Integrity verification must flag the violation!
    res = AuditService.verify_integrity(db_session)
    assert res["is_valid"] is False
    assert "Hash chain broken" in res["message"]
