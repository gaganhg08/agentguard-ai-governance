import pytest
from backend.rbac_service import RBACService
from backend.policy_engine import PolicyEngine
from backend.agent_service import AgentService
from backend.models import Permission, Role, Agent, AuditLog
from backend.schemas import AgentCreate

def test_roles_listing(db_session):
    roles = RBACService.list_roles(db_session)
    role_names = [r["name"] for r in roles]
    assert "Customer Support" in role_names
    assert "Finance" in role_names
    assert "IT Administrator" in role_names

def test_least_privilege_customer_support(db_session):
    """
    Customer Support must have:
    - customer:read (ALLOW)
    - ticket:create (ALLOW)
    - refund:request (ALLOW)
    And must NOT have:
    - refund:approve (DENY)
    - system:manage (DENY)
    """
    # 1. Allowed actions
    allowed_actions = ["customer:read", "ticket:create", "refund:request"]
    for action in allowed_actions:
        res = PolicyEngine.evaluate(
            db=db_session,
            agent_id="agent-support-01",
            tool_name=action,
            parameters={}
        )
        assert res.decision == "ALLOW", f"Expected {action} to be ALLOW for Customer Support"

    # 2. Denied actions (Least Privilege)
    forbidden_actions = ["refund:approve", "system:manage"]
    for action in forbidden_actions:
        res = PolicyEngine.evaluate(
            db=db_session,
            agent_id="agent-support-01",
            tool_name=action,
            parameters={}
        )
        assert res.decision == "DENY", f"Expected {action} to be DENIED for Customer Support"
        assert "RBAC Denied" in res.reason

def test_least_privilege_finance(db_session):
    """
    Finance role must have:
    - customer:read (ALLOW)
    - refund:approve (REQUIRE_APPROVAL or ALLOW depending on sensitivity)
    And must NOT have:
    - system:manage (DENY)
    """
    # Allowed: customer:read
    res_read = PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-finance-01",
        tool_name="customer:read",
        parameters={}
    )
    assert res_read.decision == "ALLOW"

    # Sensitive approval: refund:approve
    res_appr = PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-finance-01",
        tool_name="refund:approve",
        parameters={"amount": 250.0}
    )
    assert res_appr.decision in ["ALLOW", "REQUIRE_APPROVAL"]

    # Denied: system:manage
    res_sys = PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-finance-01",
        tool_name="system:manage",
        parameters={}
    )
    assert res_sys.decision == "DENY"
    assert "RBAC Denied" in res_sys.reason

def test_least_privilege_it_admin(db_session):
    """
    IT Administrator role must have:
    - system:manage (REQUIRE_APPROVAL or ALLOW)
    And must NOT have:
    - refund:approve (DENY)
    """
    # Create an agent with IT Administrator role
    new_agent = AgentCreate(
        id="agent-it-sre-01",
        name="Lead SRE Bot",
        role="IT Administrator",
        is_active=True
    )
    AgentService.create_agent(db_session, new_agent)

    # Allowed / Sensitive: system:manage
    res_sys = PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-it-sre-01",
        tool_name="system:manage",
        parameters={"action": "restart_daemon"}
    )
    assert res_sys.decision in ["ALLOW", "REQUIRE_APPROVAL"]

    # Denied: refund:approve
    res_ref = PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-it-sre-01",
        tool_name="refund:approve",
        parameters={"amount": 50.0}
    )
    assert res_ref.decision == "DENY"
    assert "RBAC Denied" in res_ref.reason

def test_default_deny_unassigned_permission(db_session):
    """Verify that any unrecognized or unassigned permission is denied."""
    res = PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-support-01",
        tool_name="arbitrary:unauthorized_action",
        parameters={}
    )
    assert res.decision == "DENY"

def test_prevent_unauthorized_permission_changes(db_session):
    """Security Requirement: Prevent unauthorized permission changes."""
    # Attempting to grant permission without admin authorization identity
    with pytest.raises(PermissionError) as exc_info:
        RBACService.grant_permission(
            db=db_session,
            role="Customer Support",
            tool_name="system:manage",
            authorized_by="unauthorized"
        )
    assert "Access Denied" in str(exc_info.value)

    with pytest.raises(PermissionError):
        RBACService.grant_permission(
            db=db_session,
            role="Customer Support",
            tool_name="system:manage",
            authorized_by=""
        )

def test_authorized_permission_modification_and_auditing(db_session):
    """
    Authorized administrator grants permission, immediately reflected in RBAC check,
    and verified in the tamper-evident audit log.
    """
    perm = RBACService.grant_permission(
        db=db_session,
        role="Customer Support",
        tool_name="system:manage",
        action_type="admin",
        requires_approval=True,
        authorized_by="secops_lead_carol"
    )
    assert perm.id is not None
    assert perm.tool_name == "system:manage"

    # Now Customer Support can invoke system:manage (requires approval)
    res = PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-support-01",
        tool_name="system:manage",
        parameters={}
    )
    assert res.decision == "REQUIRE_APPROVAL"

    # Check audit log record
    log = db_session.query(AuditLog).filter(
        AuditLog.tool_name == "grant_permission"
    ).order_by(AuditLog.id.desc()).first()
    assert log is not None
    assert log.approver == "secops_lead_carol"
    assert "secops_lead_carol" in log.reason

def test_assign_role_to_agent_lifecycle(db_session):
    """Test reassigning an agent's role updates their effective permissions."""
    # agent-support-01 cannot manage system initially
    # Reassign agent to IT Administrator
    RBACService.assign_role_to_agent(
        db=db_session,
        agent_id="agent-support-01",
        new_role="IT Administrator",
        authorized_by="sysadmin_alice"
    )
    agent = AgentService.get_agent(db_session, "agent-support-01")
    assert agent.role == "IT Administrator"

    # Now can manage system
    res = PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-support-01",
        tool_name="system:manage",
        parameters={}
    )
    assert res.decision in ["ALLOW", "REQUIRE_APPROVAL"]

def test_permission_matrix_generation(db_session):
    """Test generating full role x permission cross-matrix."""
    matrix = RBACService.get_permission_matrix(db_session)
    assert "roles" in matrix
    assert "permissions" in matrix
    assert "matrix" in matrix
    assert "Customer Support" in matrix["roles"]
    assert "customer:read" in matrix["permissions"]
    assert matrix["matrix"]["customer:read"]["Customer Support"]["granted"] is True
