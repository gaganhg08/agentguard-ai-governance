import pytest
from pydantic import ValidationError
from backend.agent_service import AgentService
from backend.policy_engine import PolicyEngine
from backend.schemas import AgentCreate, AgentUpdate, AgentResponse, AgentDetailResponse
from backend.models import Agent

def test_three_sample_agents_exist(db_session):
    """Verify Customer Support, Finance, and IT Admin sample agents are seeded."""
    support_agent = AgentService.get_agent(db_session, "agent-support-01")
    assert support_agent is not None
    assert support_agent.role == "Customer Support"
    assert "Support" in support_agent.name

    finance_agent = AgentService.get_agent(db_session, "agent-finance-01")
    assert finance_agent is not None
    assert finance_agent.role == "Finance"
    assert "Financial" in finance_agent.name or "Finance" in finance_agent.name

    it_agent = AgentService.get_agent(db_session, "agent-it-01")
    assert it_agent is not None
    assert it_agent.role == "IT Admin"
    assert "DevOps" in it_agent.name or "IT" in it_agent.name

def test_create_and_get_agent(db_session):
    """Test registering a new agent with valid schema."""
    new_agent = AgentCreate(
        id="agent-audit-01",
        name="Compliance Auditor Bot",
        role="Security Ops",
        description="Audits access records and compliance reports",
        is_active=True,
        api_key="super_secret_token_123"
    )
    created = AgentService.create_agent(db_session, new_agent)
    assert created.id == "agent-audit-01"
    assert created.name == "Compliance Auditor Bot"
    assert created.role == "Security Ops"

    fetched = AgentService.get_agent(db_session, "agent-audit-01")
    assert fetched is not None
    assert fetched.role == "Security Ops"
    # Verify API key is hashed, never plaintext
    assert fetched.api_key_hash is not None
    assert fetched.api_key_hash != "super_secret_token_123"

def test_duplicate_agent_id_rejected(db_session):
    """Security Requirement: Every agent must have a unique ID."""
    dup = AgentCreate(
        id="agent-support-01",
        name="Duplicate Support",
        role="Customer Support",
        is_active=True
    )
    with pytest.raises(ValueError) as exc:
        AgentService.create_agent(db_session, dup)
    assert "already exists" in str(exc.value)

def test_invalid_agent_id_format_rejected():
    """Verify ID regex and length validation."""
    with pytest.raises(ValidationError):
        AgentCreate(
            id="a",  # too short (< 3 chars)
            name="Valid Name",
            role="Finance"
        )

    with pytest.raises(ValidationError):
        AgentCreate(
            id="invalid id with spaces!",  # invalid chars
            name="Valid Name",
            role="Finance"
        )

def test_search_and_filter_agents(db_session):
    """Test filtering agents by search keyword, role, and active status."""
    # Search by keyword
    results = AgentService.list_agents(db_session, search="support")
    assert len(results) >= 1
    assert any("support" in a.name.lower() or "support" in a.id.lower() for a in results)

    # Filter by role
    finance_results = AgentService.list_agents(db_session, role="Finance")
    assert len(finance_results) >= 1
    assert all(a.role == "Finance" for a in finance_results)

    # Filter by active status
    active_results = AgentService.list_agents(db_session, is_active=True)
    assert all(a.is_active is True for a in active_results)

    inactive_results = AgentService.list_agents(db_session, is_active=False)
    assert all(a.is_active is False for a in inactive_results)

def test_edit_agent_information(db_session):
    """Test modifying agent name, role, description, and status."""
    updates = AgentUpdate(
        name="Senior Support Assistant",
        role="Customer Support",
        description="Updated tier-2 support scope",
        is_active=True
    )
    updated = AgentService.update_agent(db_session, "agent-support-01", updates)
    assert updated is not None
    assert updated.name == "Senior Support Assistant"
    assert updated.description == "Updated tier-2 support scope"

def test_toggle_agent_status(db_session):
    """Test activating and deactivating an agent identity."""
    agent = AgentService.get_agent(db_session, "agent-support-01")
    assert agent.is_active is True

    toggled = AgentService.toggle_agent_status(db_session, "agent-support-01")
    assert toggled.is_active is False

    toggled_again = AgentService.toggle_agent_status(db_session, "agent-support-01")
    assert toggled_again.is_active is True

def test_inactive_agent_blocked_from_execution(db_session):
    """Security Requirement: Inactive agents must not execute actions."""
    # Ensure agent is deactivated
    AgentService.update_agent(db_session, "agent-support-01", AgentUpdate(is_active=False))

    res = PolicyEngine.evaluate(
        db=db_session,
        agent_id="agent-support-01",
        tool_name="search_faq",
        parameters={"query": "return policy"}
    )
    assert res.decision == "DENY"
    assert "DEACTIVATED" in res.reason
    assert "AGENT_INACTIVE" in res.guardrail_flags

def test_credentials_not_exposed_in_response(db_session):
    """Security Requirement: Do not expose sensitive credentials in responses."""
    detail = AgentService.get_agent_detail(db_session, "agent-support-01")
    assert detail is not None
    assert "api_key" not in detail
    assert "api_key_hash" not in detail

    # Verify Pydantic response models do not have credential fields
    res_schema = AgentResponse.model_validate(AgentService.get_agent(db_session, "agent-support-01"))
    assert not hasattr(res_schema, "api_key")
    assert not hasattr(res_schema, "api_key_hash")

def test_agent_detail_activity_metrics(db_session):
    """Test detail inspection with calculated metrics and allowed tools."""
    detail = AgentService.get_agent_detail(db_session, "agent-support-01")
    assert detail is not None
    assert "total_evaluations" in detail
    assert "allowed_actions" in detail
    assert "blocked_actions" in detail
    assert "pending_approvals" in detail
    assert "allowed_tools" in detail
    assert isinstance(detail["allowed_tools"], list)
    # Customer support has search_faq, view_order, send_email, issue_refund
    assert "search_faq" in detail["allowed_tools"]
