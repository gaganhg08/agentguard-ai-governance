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

def test_audit_log_records_resource_and_approval_status(db_session):
    # Verify resource and approval status recording
    entry = AuditService.log_event(
        db=db_session,
        agent_id="agent-finance-01",
        agent_name="Financial Bot",
        agent_role="Finance",
        tool_name="process_payment",
        resource="ledger:general-corporate",
        parameters={"recipient": "ACC-99", "amount": 2500.0},
        decision="REQUIRE_APPROVAL",
        reason="Exceeds disbursement ceiling",
        approver="lead_auditor_dave",
        execution_status="PENDING_APPROVAL"
    )
    assert entry.agent_id == "agent-finance-01"
    assert entry.tool_name == "process_payment"
    assert entry.resource == "ledger:general-corporate"
    assert entry.decision == "REQUIRE_APPROVAL"
    assert entry.approver == "lead_auditor_dave"
    assert entry.execution_status == "PENDING_APPROVAL"
    assert entry.timestamp is not None

def test_audit_log_filters_by_agent_decision_and_search(db_session):
    # Log distinct actions to test search and filters
    AuditService.log_event(
        db=db_session,
        agent_id="agent-secops-01",
        agent_name="Security Ops Sentinel",
        agent_role="Security Ops",
        tool_name="isolate_host",
        resource="server:compromised-node-7",
        parameters={"host": "worker-7"},
        decision="ALLOW",
        reason="Security quarantine initiated"
    )

    # Filter by agent_id
    secops_logs = AuditService.get_logs(db=db_session, agent_id="agent-secops-01")
    assert any(l.agent_id == "agent-secops-01" for l in secops_logs)

    # Filter by decision
    deny_logs = AuditService.get_logs(db=db_session, decision="DENY")
    for l in deny_logs:
        assert l.decision == "DENY"

    # Search query
    searched = AuditService.get_logs(db=db_session, search_query="compromised-node-7")
    assert len(searched) >= 1
    assert any("compromised-node-7" in s.resource for s in searched)

def test_audit_log_prevent_deletion_and_modification(db_session):
    # Security Rule: Audit logs are append-only. Deletion and modification must be barred.
    with pytest.raises(PermissionError) as del_err:
        AuditService.delete_log(db_session, log_id=1)
    assert "append-only" in str(del_err.value).lower()

    with pytest.raises(PermissionError) as mod_err:
        AuditService.update_log(db_session, log_id=1, reason="altered reason")
    assert "cannot be modified" in str(mod_err.value).lower()

def test_policy_evaluation_and_tool_execution_logged_automatically(db_session):
    from backend.policy_engine import PolicyEngine
    
    initial_count = len(AuditService.get_logs(db=db_session, limit=1000))
    
    # Run policy evaluation
    PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-support-01",
        tool_name="search_faq",
        parameters={"query": "warranty claims"}
    )
    
    new_count = len(AuditService.get_logs(db=db_session, limit=1000))
    assert new_count == initial_count + 1
