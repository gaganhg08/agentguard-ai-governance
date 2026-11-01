from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db
from backend.models import Agent, Permission, PolicyRule
from backend.audit_service import AuditService

def seed_database(db: Session = None):
    should_close = False
    if db is None:
        init_db()
        db = SessionLocal()
        should_close = True

    try:
        # Check if already seeded
        if db.query(Agent).count() > 0:
            return

        # 1. SEED AGENTS
        sample_agents = [
            Agent(
                id="agent-support-01",
                name="Frontline Support Assistant",
                role="Customer Support",
                description="Handles customer queries, FAQ searches, order lookup, and standard customer refunds under $100.",
                is_active=True
            ),
            Agent(
                id="agent-finance-01",
                name="Financial Operations Bot",
                role="Finance",
                description="Processes outbound corporate disbursements, vendor invoices, financial reports, and ledger adjustments.",
                is_active=True
            ),
            Agent(
                id="agent-it-01",
                name="Cloud DevOps & Admin Agent",
                role="IT Admin",
                description="Monitors server metrics and initiates service restarts or firewall modifications with human authorization.",
                is_active=True
            ),
            Agent(
                id="agent-inactive-demo",
                name="Decommissioned Legacy Bot",
                role="Customer Support",
                description="Test agent purposefully set to inactive to verify identity and lifecycle enforcement.",
                is_active=False
            )
        ]
        db.add_all(sample_agents)
        db.commit()

        # 2. SEED PERMISSIONS (RBAC)
        permissions = [
            # Customer Support Permissions
            Permission(role="Customer Support", tool_name="search_faq", action_type="read", requires_approval=False),
            Permission(role="Customer Support", tool_name="view_order", action_type="read", requires_approval=False),
            Permission(role="Customer Support", tool_name="send_email", action_type="write", requires_approval=False),
            Permission(role="Customer Support", tool_name="issue_refund", action_type="execute", max_amount=100.0, requires_approval=False),

            # Finance Permissions
            Permission(role="Finance", tool_name="view_invoice", action_type="read", requires_approval=False),
            Permission(role="Finance", tool_name="generate_financial_report", action_type="read", requires_approval=False),
            Permission(role="Finance", tool_name="process_payment", action_type="execute", max_amount=5000.0, requires_approval=False),
            Permission(role="Finance", tool_name="update_ledger", action_type="write", requires_approval=True),

            # IT Admin Permissions
            Permission(role="IT Admin", tool_name="query_server_metrics", action_type="read", requires_approval=False),
            Permission(role="IT Admin", tool_name="restart_service", action_type="admin", requires_approval=True),
            Permission(role="IT Admin", tool_name="modify_firewall", action_type="admin", requires_approval=True),
            Permission(role="IT Admin", tool_name="reset_password", action_type="admin", requires_approval=True),
        ]
        db.add_all(permissions)
        db.commit()

        # 3. INITIAL AUDIT LOG (Genesis bootstrap)
        AuditService.log_event(
            db=db,
            agent_id="system-bootstrap",
            agent_name="AgentGuard Core",
            agent_role="System",
            tool_name="system_init",
            parameters={"status": "INITIALIZED", "sample_agents_count": 4},
            decision="ALLOW",
            reason="Platform bootstrap and RBAC baseline configuration loaded.",
            risk_level="LOW",
            execution_status="EXECUTED"
        )

    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    seed_database()
    print("Database successfully initialized and seeded with baseline security policies!")
