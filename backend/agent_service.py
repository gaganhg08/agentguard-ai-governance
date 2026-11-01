import hashlib
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import or_
from sqlalchemy.orm import Session
from backend.models import Agent, Permission, AuditLog, ApprovalRequest
from backend.schemas import AgentCreate, AgentUpdate, AgentDetailResponse

class AgentService:

    @staticmethod
    def get_agent(db: Session, agent_id: str) -> Optional[Agent]:
        return db.query(Agent).filter(Agent.id == agent_id).first()

    @staticmethod
    def get_agent_detail(db: Session, agent_id: str) -> Optional[dict[str, Any]]:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None

        # Calculate metrics from actual database tables
        logs = db.query(AuditLog).filter(AuditLog.agent_id == agent_id).all()
        total_evals = len(logs)
        allowed_count = sum(1 for l in logs if l.decision == "ALLOW")
        blocked_count = sum(1 for l in logs if l.decision == "DENY")
        
        pending_count = db.query(ApprovalRequest).filter(
            ApprovalRequest.agent_id == agent_id,
            ApprovalRequest.status == "PENDING"
        ).count()

        last_log = db.query(AuditLog).filter(AuditLog.agent_id == agent_id).order_by(AuditLog.timestamp.desc()).first()
        last_active = last_log.timestamp if last_log else None

        # Fetch allowed tools for this agent's role
        perms = db.query(Permission).filter(Permission.role == agent.role).all()
        allowed_tools = [p.tool_name for p in perms]

        return {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role,
            "description": agent.description or "",
            "is_active": agent.is_active,
            "created_at": agent.created_at,
            "updated_at": agent.updated_at,
            "total_evaluations": total_evals,
            "allowed_actions": allowed_count,
            "blocked_actions": blocked_count,
            "pending_approvals": pending_count,
            "last_active": last_active,
            "allowed_tools": allowed_tools
        }

    @staticmethod
    def list_agents(
        db: Session,
        active_only: bool = False,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> list[Agent]:
        query = db.query(Agent)

        if active_only:
            query = query.filter(Agent.is_active == True)
        elif is_active is not None:
            query = query.filter(Agent.is_active == is_active)

        if role and role.strip() and role.lower() != "all":
            query = query.filter(Agent.role == role.strip())

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Agent.id.ilike(term),
                    Agent.name.ilike(term),
                    Agent.description.ilike(term)
                )
            )

        return query.order_by(Agent.created_at.desc()).all()

    @staticmethod
    def create_agent(db: Session, agent_data: AgentCreate) -> Agent:
        cleaned_id = agent_data.id.strip()
        existing = db.query(Agent).filter(Agent.id == cleaned_id).first()
        if existing:
            raise ValueError(f"Agent with ID '{cleaned_id}' already exists.")

        # Hash API key if provided to ensure credentials are never stored in plaintext
        key_hash = None
        if agent_data.api_key and agent_data.api_key.strip():
            key_hash = hashlib.sha256(agent_data.api_key.strip().encode("utf-8")).hexdigest()

        now = datetime.now(timezone.utc)
        new_agent = Agent(
            id=cleaned_id,
            name=agent_data.name.strip(),
            role=agent_data.role.strip(),
            description=agent_data.description.strip() if agent_data.description else "",
            is_active=agent_data.is_active,
            api_key_hash=key_hash,
            created_at=now,
            updated_at=now
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

        if updates.name is not None and updates.name.strip():
            agent.name = updates.name.strip()
        if updates.role is not None and updates.role.strip():
            agent.role = updates.role.strip()
        if updates.description is not None:
            agent.description = updates.description.strip()
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

    @staticmethod
    def get_agent_activity(db: Session, agent_id: str, limit: int = 50) -> list[AuditLog]:
        return db.query(AuditLog).filter(
            AuditLog.agent_id == agent_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
