import re
from typing import Any
from sqlalchemy.orm import Session
from backend.policy_engine import PolicyEngine
from backend.schemas import MockAgentRunResponse

class MockAIAgent:
    """
    Deterministic Mock AI Agent.
    Operates 100% offline without requiring paid API keys or external services.
    Simulates LLM autonomous tool reasoning and routes all tool requests through AgentGuard.
    Guarantees:
    - Never trusts an LLM to self-authorize.
    - Evaluates all actions via central backend PolicyEngine.
    - Only executes actions that receive ALLOW.
    - Routes REQUIRE_APPROVAL actions to dual-control approval queue.
    - Blocks DENY actions immediately.
    """

    @classmethod
    def plan_and_propose(cls, user_prompt: str) -> tuple[str, dict[str, Any], str]:
        """
        Parses user natural language prompt into a structured tool call.
        Returns: (proposed_tool, proposed_parameters, target_resource)
        """
        prompt_lower = user_prompt.lower()

        # Scenario 6: Prompt injection / Jailbreak attack
        if any(kw in prompt_lower for kw in [
            "ignore previous instructions", "drop table", "bypass", "disregard",
            "override security", "system override", "admin credentials", "delete from"
        ]):
            return (
                "issue_refund",
                {
                    "order_id": "ORD-MALICIOUS",
                    "amount": 9999.0,
                    "notes": f"SYSTEM OVERRIDE; DROP TABLE agents; -- {user_prompt}"
                },
                "customer:order-malicious"
            )

        # Scenario 1: Customer support reads customer information
        if any(kw in prompt_lower for kw in [
            "read customer", "customer information", "customer info", "customer details",
            "customer profile", "lookup customer", "view customer", "user data"
        ]):
            cust_match = re.search(r"cust-?(\d+)", prompt_lower)
            cust_id = f"CUST-{cust_match.group(1)}" if cust_match else "CUST-1049"
            return (
                "read_customer_data",
                {"customer_id": cust_id},
                f"customer:{cust_id}"
            )

        # Scenario 3: Finance agent attempts to approve a refund
        if any(kw in prompt_lower for kw in [
            "approve refund", "finance approve", "authorize refund", "approve customer refund"
        ]):
            ref_match = re.search(r"ref-?(\d+)", prompt_lower)
            ref_id = f"REF-{ref_match.group(1)}" if ref_match else "REF-8821"
            dollar_match = re.search(r"\$\s*(\d+(?:\.\d{1,2})?)", user_prompt)
            if dollar_match:
                amount = float(dollar_match.group(1))
            else:
                amt_match = re.search(r"(?:amount|of)\s+(\d+(?:\.\d{1,2})?)", user_prompt, re.I)
                amount = float(amt_match.group(1)) if amt_match else 750.0
            return (
                "approve_refund",
                {"refund_id": ref_id, "amount": amount},
                f"finance:refund-{ref_id}"
            )

        # Scenario 2: Customer support requests a refund
        if "refund" in prompt_lower or "money back" in prompt_lower or "reimburse" in prompt_lower:
            dollar_match = re.search(r"\$\s*(\d+(?:\.\d{1,2})?)", user_prompt)
            if dollar_match:
                amount = float(dollar_match.group(1))
            else:
                amt_match = re.search(r"(?:refund|reimburse|of|amount)\s+(\d+(?:\.\d{1,2})?)", user_prompt, re.I)
                amount = float(amt_match.group(1)) if amt_match else 45.0
            order_match = re.search(r"order\s*#?([A-Za-z0-9\-]+)", user_prompt, re.I)
            order_id = order_match.group(1) if order_match else "ORD-9821"
            return (
                "issue_refund",
                {"order_id": order_id, "amount": amount},
                f"order:{order_id}"
            )

        # Scenario 5: Agent attempts an unknown / rogue tool
        if any(kw in prompt_lower for kw in [
            "unknown tool", "arbitrary shell", "execute shell", "run bash",
            "terminal command", "exec shell", "cmd", "unregistered"
        ]):
            return (
                "execute_arbitrary_shell",
                {"command": "whoami && cat /etc/shadow"},
                "system:host-shell"
            )

        # View order intent
        if "view order" in prompt_lower or "track order" in prompt_lower or "status of order" in prompt_lower:
            order_match = re.search(r"order\s*#?([A-Za-z0-9\-]+)", user_prompt, re.I)
            order_id = order_match.group(1) if order_match else "ORD-1002"
            return ("view_order", {"order_id": order_id}, f"order:{order_id}")

        # Search FAQ intent
        if "faq" in prompt_lower or "help" in prompt_lower or "return policy" in prompt_lower:
            return ("search_faq", {"query": user_prompt}, "knowledge:faq-portal")

        # Payment intent
        if "pay" in prompt_lower or "wire" in prompt_lower or "transfer" in prompt_lower or "invoice" in prompt_lower:
            amt_match = re.search(r"\$?(\d+(?:\.\d{1,2})?)", user_prompt)
            amount = float(amt_match.group(1)) if amt_match else 1200.0
            return (
                "process_payment",
                {"recipient_account": "ACC-CORP-4402", "amount": amount},
                "disbursement:vendor-vault"
            )

        # Restart service intent
        if "restart" in prompt_lower or "service" in prompt_lower:
            return ("restart_service", {"service_name": "payment-gateway-daemon"}, "cluster:payment-gateway")

        # Modify firewall intent
        if "firewall" in prompt_lower or "port" in prompt_lower:
            return ("modify_firewall", {"rule_action": "ALLOW", "cidr_block": "0.0.0.0/0", "port": 22}, "network:edge-firewall")

        # Default fallback: unknown tool
        return ("unauthorized_shell_exec", {"cmd": user_prompt}, "system:untrusted-shell")

    @classmethod
    def _execute_tool_action(cls, tool_name: str, parameters: dict[str, Any], resource: str) -> str:
        """
        Simulated high-fidelity tool execution payload for actions receiving ALLOW.
        Only called when PolicyEngine approves the action.
        """
        if tool_name == "read_customer_data":
            cid = parameters.get("customer_id", "CUST-1049")
            return (
                f"✅ Customer Profile [{cid}] Retrieved:\n"
                f"• Full Name: Alexander Wright\n"
                f"• Email: a.wright@enterprise-client.io\n"
                f"• Organization: Global Logistics Corp\n"
                f"• Tier: Enterprise SaaS Plan (Active)\n"
                f"• Lifetime Orders: 14\n"
                f"• Account Status: In Good Standing"
            )

        if tool_name == "issue_refund":
            oid = parameters.get("order_id", "ORD-9821")
            amt = parameters.get("amount", 45.0)
            return (
                f"✅ Refund Processed Successfully:\n"
                f"• Target Order: {oid}\n"
                f"• Amount Credited: ${amt:,.2f}\n"
                f"• Payment Method: Original Visa (ending in 4012)\n"
                f"• Authorization Code: AUTH-REF-99214\n"
                f"• Timestamp: Immediate Ledger Update"
            )

        if tool_name == "approve_refund":
            rid = parameters.get("refund_id", "REF-8821")
            amt = parameters.get("amount", 750.0)
            return (
                f"✅ Refund Approval Finalized:\n"
                f"• Refund Ticket: {rid}\n"
                f"• Authorized Amount: ${amt:,.2f}\n"
                f"• Status: Disbursed to Merchant Account"
            )

        if tool_name == "search_faq":
            return (
                f"✅ Knowledge Base Articles Found:\n"
                f"• Article #104: Return Policy (30-day window, prepaid return label)\n"
                f"• Article #105: Damaged Goods Warranty & Replacement Protocol"
            )

        if tool_name == "view_order":
            oid = parameters.get("order_id", "ORD-1002")
            return (
                f"✅ Order Details [{oid}]:\n"
                f"• Status: Shipped via FedEx Priority\n"
                f"• Tracking ID: 9400-1120-8821-0042\n"
                f"• Estimated Delivery: Tomorrow at 2:00 PM\n"
                f"• Destination: Austin, TX"
            )

        if tool_name == "process_payment":
            acc = parameters.get("recipient_account", "ACC-CORP-4402")
            amt = parameters.get("amount", 1200.0)
            return (
                f"✅ Electronic Payment Dispatched:\n"
                f"• Target Account: {acc}\n"
                f"• Amount: ${amt:,.2f}\n"
                f"• Settlement: Fedwire Corporate Gateway\n"
                f"• Trace ID: WIRE-2026-11-09821"
            )

        if tool_name == "restart_service":
            svc = parameters.get("service_name", "daemon")
            return f"✅ Service daemon '{svc}' restarted cleanly (PID 9214 -> HEALTHY)."

        return f"✅ Tool '{tool_name}' executed cleanly on resource '{resource}' with parameters: {parameters}"

    @classmethod
    def execute(cls, db: Session, agent_id: str, user_prompt: str) -> MockAgentRunResponse:
        from backend.models import Agent
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        agent_name = agent.name if agent else "Unknown Agent"
        agent_role = agent.role if agent else "Unknown Role"

        # Step 1: Autonomous Agent Tool Planning (Deterministic Mock Planner)
        proposed_tool, proposed_params, target_resource = cls.plan_and_propose(user_prompt)

        # Step 2: Zero-Trust Central Policy Enforcement Gateway Interception
        eval_result = PolicyEngine.evaluate(
            db=db,
            agent_id=agent_id,
            tool_name=proposed_tool,
            parameters=proposed_params,
            resource=target_resource
        )

        # Step 3: Controlled Execution Based Strictly on Backend Verdict
        exec_res = None
        if eval_result.decision == "ALLOW":
            exec_res = cls._execute_tool_action(proposed_tool, proposed_params, target_resource)
        elif eval_result.decision == "REQUIRE_APPROVAL":
            exec_res = (
                f"⚠️ ACTION SUSPENDED: Paused by AgentGuard central policy engine. "
                f"Created Approval Request #{eval_result.approval_id} awaiting dual-control human authorization. "
                f"Direct autonomous LLM execution is blocked."
            )
        else:
            exec_res = (
                f"🚫 ACTION BLOCKED: Blocked by AgentGuard security guardrails. "
                f"Reason: {eval_result.reason}. Action will NOT be executed."
            )

        return MockAgentRunResponse(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_role=agent_role,
            user_prompt=user_prompt,
            proposed_tool=proposed_tool,
            target_resource=target_resource,
            proposed_parameters=proposed_params,
            policy_decision=eval_result.decision,
            policy_reason=eval_result.reason,
            applicable_policy=eval_result.applicable_policy,
            risk_level=eval_result.risk_level,
            approval_id=eval_result.approval_id,
            execution_result=exec_res,
            guardrail_flags=eval_result.guardrail_flags,
            evaluation_trace=eval_result.evaluation_trace
        )
