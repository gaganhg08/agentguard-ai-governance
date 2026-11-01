import pytest
from backend.agent_service import AgentService
from backend.schemas import AgentCreate, AgentUpdate

def test_list_agents(db_session):
    agents = AgentService.list_agents(db_session)
    assert len(agents) >= 3
    agent_ids = [a.id for a in agents]
    assert "agent-support-01" in agent_ids
    assert "agent-finance-01" in agent_ids
    assert "agent-it-01" in agent_ids

def test_create_and_get_agent(db_session):
    new_agent = AgentCreate(
        id="agent-audit-01",
        name="Compliance Auditor Bot",
        role="Auditor",
        description="Audits access records",
        is_active=True
    )
    created = AgentService.create_agent(db_session, new_agent)
    assert created.id == "agent-audit-01"
    assert created.name == "Compliance Auditor Bot"

    fetched = AgentService.get_agent(db_session, "agent-audit-01")
    assert fetched is not None
    assert fetched.role == "Auditor"

def test_duplicate_agent_id_rejected(db_session):
    dup = AgentCreate(
        id="agent-support-01",
        name="Duplicate Support",
        role="Customer Support",
        is_active=True
    )
    with pytest.raises(ValueError):
        AgentService.create_agent(db_session, dup)

def test_toggle_agent_status(db_session):
    agent = AgentService.get_agent(db_session, "agent-support-01")
    assert agent.is_active is True

    toggled = AgentService.toggle_agent_status(db_session, "agent-support-01")
    assert toggled.is_active is False

    toggled_again = AgentService.toggle_agent_status(db_session, "agent-support-01")
    assert toggled_again.is_active is True
