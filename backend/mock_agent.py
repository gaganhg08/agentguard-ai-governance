import re
from typing import Any
from sqlalchemy.orm import Session
from backend.policy_engine import PolicyEngine
from backend.schemas import MockAgentRunResponse

class MockAIAgent:
    """
    Autonomous Mock AI Agent.
    Operates 100% offline without requiring external API keys.
    Simulates LLM tool planning and sends all proposed actions to AgentGuard.
    """

    @classmethod
    def plan_and_propose(cls, user_prompt: str) -> tuple[str, dict[str, Any]]:
        """
        Parses user natural language prompt into a structured tool call.
        """
        prompt_lower = user_prompt.lower()

        # Check prompt injection patterns directly in prompt to demonstrate agent forwarding attack
        if "ignore previous instructions" in prompt_lower or "drop table" in prompt_lower or "bypass" in prompt_lower:
            return "issue_refund", {
                "order_id": "ORD-MALICIOUS",
                "amount": 9999,
                "notes": f"SYSTEM OVERRIDE; drop table agents; -- {user_prompt}"
            }

        # Refund intent
        if "refund" in prompt_lower or "money back" in prompt_lower:
            amt_match = re.search(r"\$?(\d+(?:\.\d{1,2})?)", user_prompt)
            amount = float(amt_match.group(1)) if amt_match else 50.0
            order_match = re.search(r"order\s*#?([A-Za-z0-9\-]+)", user_prompt, re.I)
            order_id = order_match.group(1) if order_match else "ORD-98214"
            return "issue_refund", {"order_id": order_id, "amount": amount}

        # View order intent
        if "view order" in prompt_lower or "track order" in prompt_lower or "status of order" in prompt_lower:
            order_match = re.search(r"order\s*#?([A-Za-z0-9\-]+)", user_prompt, re.I)
            order_id = order_match.group(1) if order_match else "ORD-1002"
            return "view_order", {"order_id": order_id}

        # Search FAQ intent
        if "faq" in prompt_lower or "help" in prompt_lower or "how to" in prompt_lower or "return policy" in prompt_lower:
            return "search_faq", {"query": user_prompt}

        # Payment intent
        if "pay" in prompt_lower or "wire" in prompt_lower or "transfer" in prompt_lower or "invoice" in prompt_lower:
            amt_match = re.search(r"\$?(\d+(?:\.\d{1,2})?)", user_prompt)
            amount = float(amt_match.group(1)) if amt_match else 1200.0
            return "process_payment", {"recipient_account": "ACC-CORP-4402", "amount": amount}

        # Restart service intent
        if "restart" in prompt_lower or "service" in prompt_lower:
            return "restart_service", {"service_name": "payment-gateway-daemon"}

        # Modify firewall intent
        if "firewall" in prompt_lower or "port" in prompt_lower or "block ip" in prompt_lower:
            return "modify_firewall", {"rule_action": "ALLOW", "cidr_block": "0.0.0.0/0", "port": 22}

        # Default fallback: unknown tool
        return "unauthorized_shell_exec", {"cmd": user_prompt}

    @classmethod
    def execute(cls, db: Session, agent_id: str, user_prompt: str) -> MockAgentRunResponse:
        from backend.models import Agent
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        agent_name = agent.name if agent else "Unknown Agent"
        agent_role = agent.role if agent else "Unknown Role"

        proposed_tool, proposed_params = cls.plan_and_propose(user_prompt)

        # Delegate execution proposal to Policy Engine
        eval_result = PolicyEngine.evaluate(
            db=db,
            agent_id=agent_id,
            tool_name=proposed_tool,
            parameters=proposed_params
        )

        exec_res = None
        if eval_result.decision == "ALLOW":
            exec_res = f"Success: Autonomous action executed successfully with parameters: {proposed_params}"
        elif eval_result.decision == "REQUIRE_APPROVAL":
            exec_res = f"Action paused: Created Approval Request #{eval_result.approval_id} awaiting human reviewer."
        else:
            exec_res = f"Action blocked by AgentGuard: {eval_result.reason}"

        return MockAgentRunResponse(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_role=agent_role,
            user_prompt=user_prompt,
            proposed_tool=proposed_tool,
            proposed_parameters=proposed_params,
            policy_decision=eval_result.decision,
            policy_reason=eval_result.reason,
            risk_level=eval_result.risk_level,
            approval_id=eval_result.approval_id,
            execution_result=exec_res
        )
