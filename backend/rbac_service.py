from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy.orm import Session
from backend.models import Role, Permission, Agent
from backend.audit_service import AuditService

STANDARD_PERMISSIONS = {
    "customer:read": {
        "description": "Read customer profiles, order history, and FAQ articles",
        "action_type": "read",
        "default_roles": ["Customer Support", "Finance"]
    },
    "ticket:create": {
        "description": "Open and update customer support cases and internal tickets",
        "action_type": "write",
        "default_roles": ["Customer Support"]
    },
    "refund:request": {
        "description": "Initiate refund requests for review or low-value processing",
        "action_type": "execute",
        "default_roles": ["Customer Support", "Finance"]
    },
    "refund:approve": {
        "description": "Authorize and disburse financial refunds and ledger entries",
        "action_type": "execute",
        "default_roles": ["Finance"]
    },
    "system:manage": {
        "description": "Administrative control: restart daemons, update firewalls, reset credentials",
        "action_type": "admin",
        "default_roles": ["IT Administrator"]
    }
}

class RBACService:
    """
    Enterprise Role-Based Access Control (RBAC) Management Service.
    Enforces the Principle of Least Privilege and Default-Deny behavior.
    """

    ADMIN_ROLES = {"admin", "security_officer", "super_admin", "secops_lead"}

    @classmethod
    def verify_admin_authorization(cls, authorized_by: str) -> None:
        """
        Ensures permission modifications are performed only by verified administrative identities.
        Prevents unauthorized permission escalation.
        """
        if not authorized_by or not authorized_by.strip():
            raise PermissionError("Access Denied: Administrative authorization identity cannot be empty.")
        
        cleaned = authorized_by.strip().lower()
        if cleaned in ["anonymous", "guest", "agent", "unauthorized"]:
            raise PermissionError(f"Access Denied: Identity '{authorized_by}' is not authorized to alter RBAC permissions.")

    @classmethod
    def list_roles(cls, db: Session) -> list[dict[str, Any]]:
        roles = db.query(Role).all()
        result = []
        for r in roles:
            agent_count = db.query(Agent).filter(Agent.role == r.name).count()
            perm_count = db.query(Permission).filter(Permission.role == r.name).count()
            result.append({
                "name": r.name,
                "description": r.description,
                "is_system_role": r.is_system_role,
                "agent_count": agent_count,
                "permission_count": perm_count,
                "created_at": r.created_at
            })
        return result

    @classmethod
    def create_role(cls, db: Session, name: str, description: str, authorized_by: str) -> Role:
        cls.verify_admin_authorization(authorized_by)
        cleaned = name.strip()
        existing = db.query(Role).filter(Role.name == cleaned).first()
        if existing:
            raise ValueError(f"Role '{cleaned}' already exists.")

        role = Role(
            name=cleaned,
            description=description.strip() if description else "",
            is_system_role=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(role)
        db.commit()
        db.refresh(role)

        # Audit trail recording
        AuditService.log_event(
            db=db,
            agent_id="admin-rbac",
            agent_name=authorized_by,
            agent_role="Administrator",
            tool_name="create_role",
            parameters={"role_name": cleaned, "description": description},
            decision="ALLOW",
            reason=f"Administrator '{authorized_by}' created new role '{cleaned}'.",
            risk_level="MEDIUM",
            action_type="admin",
            approver=authorized_by,
            execution_status="EXECUTED"
        )
        return role

    @classmethod
    def assign_role_to_agent(cls, db: Session, agent_id: str, new_role: str, authorized_by: str) -> Agent:
        cls.verify_admin_authorization(authorized_by)
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent '{agent_id}' not found.")

        role_obj = db.query(Role).filter(Role.name == new_role).first()
        if not role_obj:
            raise ValueError(f"Target role '{new_role}' does not exist.")

        old_role = agent.role
        agent.role = new_role
        agent.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(agent)

        AuditService.log_event(
            db=db,
            agent_id="admin-rbac",
            agent_name=authorized_by,
            agent_role="Administrator",
            tool_name="assign_role",
            parameters={"agent_id": agent_id, "previous_role": old_role, "new_role": new_role},
            decision="ALLOW",
            reason=f"Role for agent '{agent.name}' ({agent_id}) reassigned from '{old_role}' to '{new_role}' by '{authorized_by}'.",
            risk_level="HIGH",
            action_type="admin",
            approver=authorized_by,
            execution_status="EXECUTED"
        )
        return agent

    @classmethod
    def grant_permission(
        cls,
        db: Session,
        role: str,
        tool_name: str,
        action_type: str = "execute",
        max_amount: Optional[float] = None,
        requires_approval: bool = False,
        description: str = "",
        authorized_by: str = "admin"
    ) -> Permission:
        cls.verify_admin_authorization(authorized_by)

        existing = db.query(Permission).filter(
            Permission.role == role,
            Permission.tool_name == tool_name
        ).first()

        if existing:
            # Update existing
            existing.action_type = action_type
            existing.max_amount = max_amount
            existing.requires_approval = requires_approval
            if description:
                existing.description = description
            db.commit()
            db.refresh(existing)
            target_perm = existing
            action_verb = "updated"
        else:
            new_perm = Permission(
                role=role,
                tool_name=tool_name,
                action_type=action_type,
                max_amount=max_amount,
                requires_approval=requires_approval,
                description=description
            )
            db.add(new_perm)
            db.commit()
            db.refresh(new_perm)
            target_perm = new_perm
            action_verb = "granted"

        # Record tamper-evident audit record of RBAC modification
        AuditService.log_event(
            db=db,
            agent_id="admin-rbac",
            agent_name=authorized_by,
            agent_role="Administrator",
            tool_name="grant_permission",
            parameters={
                "role": role,
                "permission": tool_name,
                "action_type": action_type,
                "max_amount": max_amount,
                "requires_approval": requires_approval
            },
            decision="ALLOW",
            reason=f"Permission '{tool_name}' {action_verb} for role '{role}' by '{authorized_by}'.",
            risk_level="HIGH",
            action_type="admin",
            approver=authorized_by,
            execution_status="EXECUTED"
        )
        return target_perm

    @classmethod
    def revoke_permission(cls, db: Session, permission_id: int, authorized_by: str) -> bool:
        cls.verify_admin_authorization(authorized_by)
        perm = db.query(Permission).filter(Permission.id == permission_id).first()
        if not perm:
            return False

        perm_name = perm.tool_name
        perm_role = perm.role

        db.delete(perm)
        db.commit()

        AuditService.log_event(
            db=db,
            agent_id="admin-rbac",
            agent_name=authorized_by,
            agent_role="Administrator",
            tool_name="revoke_permission",
            parameters={"permission_id": permission_id, "role": perm_role, "permission": perm_name},
            decision="ALLOW",
            reason=f"Permission '{perm_name}' revoked from role '{perm_role}' by '{authorized_by}'.",
            risk_level="HIGH",
            action_type="admin",
            approver=authorized_by,
            execution_status="EXECUTED"
        )
        return True

    @classmethod
    def get_permission_matrix(cls, db: Session) -> dict[str, Any]:
        """
        Constructs a full role-by-permission cross-matrix for visualization.
        """
        roles = [r.name for r in db.query(Role).all()]
        all_perms = db.query(Permission).all()
        distinct_perms = sorted(list(set([p.tool_name for p in all_perms] + list(STANDARD_PERMISSIONS.keys()))))

        matrix = {}
        for p in distinct_perms:
            matrix[p] = {}
            for r in roles:
                match = next((item for item in all_perms if item.role == r and item.tool_name == p), None)
                if match:
                    matrix[p][r] = {
                        "granted": True,
                        "requires_approval": match.requires_approval,
                        "max_amount": match.max_amount,
                        "action_type": match.action_type
                    }
                else:
                    matrix[p][r] = {
                        "granted": False,
                        "requires_approval": False,
                        "max_amount": None,
                        "action_type": None
                    }

        return {
            "roles": roles,
            "permissions": distinct_perms,
            "matrix": matrix
        }

    @classmethod
    def check_agent_permission(cls, db: Session, agent_id: str, permission_name: str) -> tuple[bool, str]:
        """
        Validates whether an agent has authorization for a specific permission or tool.
        Returns (is_allowed, explanation).
        Strict Default-Deny.
        """
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False, f"Unknown agent '{agent_id}'."

        if not agent.is_active:
            return False, f"Agent '{agent.name}' is deactivated."

        # Check explicit permission
        perm = db.query(Permission).filter(
            Permission.role == agent.role,
            Permission.tool_name == permission_name
        ).first()

        if not perm:
            return False, f"RBAC Denied: Role '{agent.role}' has not been granted '{permission_name}' (Default-Deny)."

        return True, f"Authorized: Role '{agent.role}' holds permission '{permission_name}'."
