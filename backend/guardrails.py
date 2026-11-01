import re
from typing import Any
from backend.config import settings

# Registered system tools and RBAC capability permissions
REGISTERED_TOOLS: dict[str, dict[str, Any]] = {
    # Standard Enterprise Permissions
    "customer:read": {
        "description": "Read customer profiles, order history, and FAQ articles",
        "category": "support",
        "risk": "LOW",
        "required_params": []
    },
    "ticket:create": {
        "description": "Open and update customer support cases and internal tickets",
        "category": "support",
        "risk": "LOW",
        "required_params": []
    },
    "refund:request": {
        "description": "Initiate refund requests for review or low-value processing",
        "category": "finance",
        "risk": "MEDIUM",
        "required_params": []
    },
    "refund:approve": {
        "description": "Authorize and disburse financial refunds and ledger entries",
        "category": "finance",
        "risk": "HIGH",
        "required_params": []
    },
    "system:manage": {
        "description": "Administrative control: restart daemons, update firewalls, reset credentials",
        "category": "infrastructure",
        "risk": "CRITICAL",
        "required_params": []
    },

    # Specific Tool Specifications
    "read_customer_data": {
        "description": "Read customer profile, account contact information, and preferences",
        "category": "support",
        "risk": "LOW",
        "required_params": ["customer_id"]
    },
    "approve_refund": {
        "description": "Authorize and disburse pending customer refund (Mandatory Dual-Control)",
        "category": "finance",
        "risk": "HIGH",
        "required_params": ["refund_id", "amount"]
    },
    "search_faq": {
        "description": "Search knowledge base articles for customer queries",
        "category": "support",
        "risk": "LOW",
        "required_params": ["query"]
    },
    "view_order": {
        "description": "Retrieve order summary and shipment tracking",
        "category": "support",
        "risk": "LOW",
        "required_params": ["order_id"]
    },
    "send_email": {
        "description": "Send notification email to user",
        "category": "communication",
        "risk": "MEDIUM",
        "required_params": ["recipient", "subject", "body"]
    },
    "issue_refund": {
        "description": "Initiate refund back to original payment method",
        "category": "finance",
        "risk": "HIGH",
        "required_params": ["order_id", "amount"]
    },
    "view_invoice": {
        "description": "View company invoice details",
        "category": "finance",
        "risk": "LOW",
        "required_params": ["invoice_id"]
    },
    "process_payment": {
        "description": "Execute outbound electronic payment",
        "category": "finance",
        "risk": "HIGH",
        "required_params": ["recipient_account", "amount"]
    },
    "generate_financial_report": {
        "description": "Generate quarterly revenue & balance statement",
        "category": "finance",
        "risk": "LOW",
        "required_params": ["quarter", "year"]
    },
    "update_ledger": {
        "description": "Make ledger journal balance adjustment",
        "category": "finance",
        "risk": "HIGH",
        "required_params": ["account_id", "delta", "reason"]
    },
    "query_server_metrics": {
        "description": "Query CPU, Memory, and Disk utilization",
        "category": "infrastructure",
        "risk": "LOW",
        "required_params": ["server_id"]
    },
    "restart_service": {
        "description": "Restart production backend daemon",
        "category": "infrastructure",
        "risk": "CRITICAL",
        "required_params": ["service_name"]
    },
    "modify_firewall": {
        "description": "Update IP routing and firewall port rules",
        "category": "infrastructure",
        "risk": "CRITICAL",
        "required_params": ["rule_action", "cidr_block", "port"]
    },
    "reset_password": {
        "description": "Trigger password reset for corporate account",
        "category": "identity",
        "risk": "HIGH",
        "required_params": ["username"]
    }
}

class GuardrailsValidator:
    """
    Validates tool requests, inspects parameters for prompt injection / jailbreak,
    and enforces parameter safety rules.
    """

    @staticmethod
    def check_tool_registered(tool_name: str) -> tuple[bool, str]:
        """Verify tool is recognized by the platform."""
        if tool_name not in REGISTERED_TOOLS:
            return False, f"Unknown tool '{tool_name}'. Tool is not registered in system catalog."
        return True, ""

    @staticmethod
    def detect_prompt_injection(data: Any) -> list[str]:
        """
        Recursively scans strings inside parameters for prompt injection patterns.
        """
        detected: list[str] = []
        text_to_check: list[str] = []

        def extract_strings(obj: Any):
            if isinstance(obj, str):
                text_to_check.append(obj)
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    extract_strings(k)
                    extract_strings(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract_strings(item)

        extract_strings(data)

        for text in text_to_check:
            lower = text.lower()
            for keyword in settings.INJECTION_KEYWORDS:
                if keyword in lower:
                    detected.append(f"Prompt injection pattern detected: '{keyword}'")

            # Check shell metacharacters attempt
            if re.search(r"(\||;|`|\$\(.*\)|\$\{.*\})", text):
                detected.append("Potential shell metacharacters detected in argument")

            # Check SQL injection signatures
            if re.search(r"(union\s+select|drop\s+table|delete\s+from|or\s+1=1|--)", lower):
                detected.append("SQL injection signature detected in argument")

        return list(set(detected))

    @staticmethod
    def validate_tool_parameters(tool_name: str, parameters: dict[str, Any]) -> tuple[bool, str]:
        """Validate required arguments and type/value boundaries."""
        spec = REGISTERED_TOOLS.get(tool_name)
        if not spec:
            return False, f"Unknown tool '{tool_name}'"

        required = spec.get("required_params", [])
        for field in required:
            if field not in parameters or parameters[field] is None:
                return False, f"Missing required parameter '{field}' for tool '{tool_name}'"

        # Specific parameter validations
        if tool_name in ["issue_refund", "process_payment", "approve_refund"]:
            amount = parameters.get("amount")
            try:
                val = float(amount)
                if val <= 0:
                    return False, f"Transaction amount must be strictly positive (got {val})"
                if val > 1_000_000:
                    return False, f"Transaction amount exceeds hard platform limit of $1,000,000"
            except (ValueError, TypeError):
                return False, f"Invalid numeric amount '{amount}'"

        if tool_name == "modify_firewall":
            port = parameters.get("port")
            try:
                port_val = int(port)
                if not (1 <= port_val <= 65535):
                    return False, f"Port must be between 1 and 65535 (got {port_val})"
            except (ValueError, TypeError):
                return False, f"Invalid port value '{port}'"

        return True, ""

    @staticmethod
    def calculate_risk_level(tool_name: str, parameters: dict[str, Any]) -> str:
        """Determines risk level based on tool spec and parameter values."""
        spec = REGISTERED_TOOLS.get(tool_name, {})
        base_risk = spec.get("risk", "MEDIUM")

        if tool_name == "issue_refund":
            amount = float(parameters.get("amount", 0))
            if amount > settings.REFUND_APPROVAL_THRESHOLD:
                return "HIGH"
            return "LOW"

        if tool_name == "process_payment":
            amount = float(parameters.get("amount", 0))
            if amount > settings.PAYMENT_APPROVAL_THRESHOLD:
                return "HIGH"
            return "MEDIUM"

        return base_risk
