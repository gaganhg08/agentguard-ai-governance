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
