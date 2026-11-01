from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from backend.models import Agent, Permission
from backend.schemas import AgentCreate, AgentUpdate

class AgentService:

    @staticmethod
    def get_agent(db: Session, agent_id: str) -> Optional[Agent]:
        return db.query(Agent).filter(Agent.id == agent_id).first()

    @staticmethod
    def list_agents(db: Session, active_only: bool = False) -> list[Agent]:
        query = db.query(Agent)
        if active_only:
            query = query.filter(Agent.is_active == True)
        return query.order_by(Agent.created_at.desc()).all()

    @staticmethod
    def create_agent(db: Session, agent_data: AgentCreate) -> Agent:
        existing = db.query(Agent).filter(Agent.id == agent_data.id).first()
        if existing:
            raise ValueError(f"Agent with ID '{agent_data.id}' already exists.")

        new_agent = Agent(
            id=agent_data.id,
            name=agent_data.name,
            role=agent_data.role,
            description=agent_data.description or "",
            is_active=agent_data.is_active,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        return new_agent

    @staticmethod
    def update_agent(db: Session, agent_id: str, updates: AgentUpdate) -> Optional[Agent]:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None

        if updates.name is not None:
            agent.name = updates.name
        if updates.role is not None:
            agent.role = updates.role
        if updates.description is not None:
            agent.description = updates.description
        if updates.is_active is not None:
            agent.is_active = updates.is_active

        agent.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def toggle_agent_status(db: Session, agent_id: str) -> Optional[Agent]:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None
        agent.is_active = not agent.is_active
        agent.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def delete_agent(db: Session, agent_id: str) -> bool:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False
        db.delete(agent)
        db.commit()
        return True
