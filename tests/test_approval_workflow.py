import pytest
from backend.policy_engine import PolicyEngine
from backend.approval_service import ApprovalService
from backend.models import ApprovalRequest

def test_approval_request_lifecycle(db_session):
    # Trigger an approval-required action
    eval_res = PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-it-01",
        tool_name="restart_service",
        parameters={"service_name": "auth-gateway"}
    )
    assert eval_res.decision == "REQUIRE_APPROVAL"
    req_id = eval_res.approval_id
    assert req_id is not None

    # Check pending list
    pending = ApprovalService.get_pending_requests(db_session)
    assert any(p.id == req_id for p in pending)

    # Human Reviewer approves
    reviewed = ApprovalService.review_request(
        db=db_session,
        request_id=req_id,
        reviewer="lead_devops_bob",
        decision="APPROVE",
        reviewer_notes="Verified maintenance window"
    )
    assert reviewed.status == "APPROVED"
    assert reviewed.reviewer == "lead_devops_bob"
    assert "SUCCESS" in reviewed.execution_result

def test_approval_rejection_lifecycle(db_session):
    eval_res = PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-it-01",
        tool_name="restart_service",
        parameters={"service_name": "billing-daemon"}
    )
    req_id = eval_res.approval_id

    # Human Reviewer rejects
    reviewed = ApprovalService.review_request(
        db=db_session,
        request_id=req_id,
        reviewer="security_officer_carol",
        decision="REJECT",
        reviewer_notes="Peak business hours"
    )
    assert reviewed.status == "REJECTED"
    assert reviewed.reviewer == "security_officer_carol"
    assert "REJECTED" in reviewed.execution_result

def test_agent_self_approval_blocked(db_session):
    eval_res = PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-it-01",
        tool_name="restart_service",
        parameters={"service_name": "database-cluster"}
    )
    req_id = eval_res.approval_id

    # Attempt self-approval using agent ID
    with pytest.raises(PermissionError) as exc_info:
        ApprovalService.review_request(
            db=db_session,
            request_id=req_id,
            reviewer="agent-it-01",
            decision="APPROVE"
        )
    assert "cannot approve its own action" in str(exc_info.value)

def test_approval_request_records_resource_and_timestamp(db_session):
    # Verify that resource and review timestamp are recorded
    req = ApprovalService.create_request(
        db=db_session,
        agent_id="agent-finance-01",
        agent_name="Financial Operations Bot",
        agent_role="Finance",
        tool_name="process_payment",
        parameters={"recipient_account": "ACC-CORP", "amount": 3000.0},
        reason="Disbursement exceeds ceiling",
        resource="vault:finance-treasury"
    )
    assert req.resource == "vault:finance-treasury"
    assert req.status == "PENDING"
    assert req.reviewed_at is None

    # Review request
    reviewed = ApprovalService.review_request(
        db=db_session,
        request_id=req.id,
        reviewer="cfo_sarah",
        decision="APPROVE",
        reviewer_notes="Verified invoice #9921 against vendor ledger"
    )
    assert reviewed.status == "APPROVED"
    assert reviewed.reviewer == "cfo_sarah"
    assert reviewed.reviewed_at is not None
    assert "Verified invoice" in reviewed.reviewer_notes

def test_approval_status_updated_in_database(db_session):
    # Verify persistent database update
    req = ApprovalService.create_request(
        db=db_session,
        agent_id="agent-it-01",
        agent_name="Cloud DevOps Sentinel",
        agent_role="IT Admin",
        tool_name="modify_firewall",
        parameters={"rule_action": "ALLOW", "port": 22},
        reason="Sensitive network change"
    )
    req_id = req.id

    # Review as REJECT
    ApprovalService.review_request(
        db=db_session,
        request_id=req_id,
        reviewer="secops_lead_carol",
        decision="REJECT",
        reviewer_notes="Port 22 SSH must not be opened directly"
    )

    # Fetch fresh from database
    db_record = db_session.query(ApprovalRequest).filter(ApprovalRequest.id == req_id).first()
    assert db_record is not None
    assert db_record.status == "REJECTED"
    assert db_record.reviewer == "secops_lead_carol"
    assert "Port 22 SSH" in db_record.reviewer_notes
