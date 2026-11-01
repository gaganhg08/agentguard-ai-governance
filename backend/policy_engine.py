from typing import Any
from sqlalchemy.orm import Session
from backend.config import settings
from backend.models import Agent, Permission, PolicyRule
from backend.guardrails import GuardrailsValidator
from backend.audit_service import AuditService
from backend.approval_service import ApprovalService
from backend.schemas import PolicyEvaluationResponse

class PolicyEngine:
    """
    Central AI Agent Security & Governance Policy Engine.
    Implements:
    - Default-Deny Security Model
    - Identity & Lifecycle Validation
    - Prompt Injection & Metacharacter Guardrails
    - Role-Based Access Control (RBAC)
    - Dynamic Sensitivity & Human-in-the-Loop Triggers
    - Immutable Audit Logging
    """

    @classmethod
    def evaluate(
        cls,
        db: Session,
        agent_id: str,
        tool_name: str,
        parameters: dict[str, Any],
        context: dict[str, Any] = None
    ) -> PolicyEvaluationResponse:
        context = context or {}
        guardrail_flags: list[str] = []

        # -------------------------------------------------------------
        # 1. AGENT IDENTITY & LIFECYCLE CHECK
        # -------------------------------------------------------------
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            reason = f"Identity Denied: Agent ID '{agent_id}' is unknown or not registered."
            AuditService.log_event(
                db=db,
                agent_id=agent_id,
                agent_name="Unknown Agent",
                agent_role="Unknown",
                tool_name=tool_name,
                parameters=parameters,
                decision="DENY",
                reason=reason,
                risk_level="HIGH",
                execution_status="BLOCKED"
            )
            return PolicyEvaluationResponse(
                decision="DENY",
                reason=reason,
                risk_level="HIGH",
                guardrail_flags=["UNKNOWN_AGENT"]
            )

        if not agent.is_active:
            reason = f"Access Denied: Agent '{agent.name}' ({agent.id}) is DEACTIVATED."
            AuditService.log_event(
                db=db,
                agent_id=agent.id,
                agent_name=agent.name,
                agent_role=agent.role,
                tool_name=tool_name,
                parameters=parameters,
                decision="DENY",
                reason=reason,
                risk_level="MEDIUM",
                execution_status="BLOCKED"
            )
            return PolicyEvaluationResponse(
                decision="DENY",
                reason=reason,
                risk_level="MEDIUM",
                guardrail_flags=["AGENT_INACTIVE"]
            )

        # -------------------------------------------------------------
        # 2. GUARDRAIL: TOOL REGISTRATION CHECK
        # -------------------------------------------------------------
        is_registered, tool_err = GuardrailsValidator.check_tool_registered(tool_name)
        if not is_registered:
            reason = f"Security Guardrail: {tool_err}"
            AuditService.log_event(
                db=db,
                agent_id=agent.id,
                agent_name=agent.name,
                agent_role=agent.role,
                tool_name=tool_name,
                parameters=parameters,
                decision="DENY",
                reason=reason,
                risk_level="HIGH",
                execution_status="BLOCKED"
            )
            return PolicyEvaluationResponse(
                decision="DENY",
                reason=reason,
                risk_level="HIGH",
                guardrail_flags=["UNREGISTERED_TOOL"]
            )

        # -------------------------------------------------------------
        # 3. GUARDRAIL: PROMPT INJECTION / ATTACK PATTERNS
        # -------------------------------------------------------------
        injection_signals = GuardrailsValidator.detect_prompt_injection(parameters)
        if injection_signals:
            guardrail_flags.extend(injection_signals)
            reason = f"Security Violation: Potential prompt injection or malicious pattern blocked: {'; '.join(injection_signals)}"
            AuditService.log_event(
                db=db,
                agent_id=agent.id,
                agent_name=agent.name,
                agent_role=agent.role,
                tool_name=tool_name,
                parameters=parameters,
                decision="DENY",
                reason=reason,
                risk_level="CRITICAL",
                guardrail_flags=guardrail_flags,
                execution_status="BLOCKED"
            )
            return PolicyEvaluationResponse(
                decision="DENY",
                reason=reason,
                risk_level="CRITICAL",
                guardrail_flags=guardrail_flags
            )

        # -------------------------------------------------------------
        # 4. GUARDRAIL: PARAMETER SCHEMA & BOUNDS VALIDATION
        # -------------------------------------------------------------
        is_valid_params, param_err = GuardrailsValidator.validate_tool_parameters(tool_name, parameters)
        if not is_valid_params:
            reason = f"Validation Failed: {param_err}"
            AuditService.log_event(
                db=db,
                agent_id=agent.id,
                agent_name=agent.name,
                agent_role=agent.role,
                tool_name=tool_name,
                parameters=parameters,
                decision="DENY",
                reason=reason,
                risk_level="MEDIUM",
                execution_status="BLOCKED"
            )
            return PolicyEvaluationResponse(
                decision="DENY",
                reason=reason,
                risk_level="MEDIUM",
                guardrail_flags=["INVALID_PARAMETERS"]
            )

        # -------------------------------------------------------------
        # 5. ROLE-BASED ACCESS CONTROL (RBAC) & PERMISSIONS
        # -------------------------------------------------------------
        # Look for explicit permission for agent's role and tool
        perm = db.query(Permission).filter(
            Permission.role == agent.role,
            Permission.tool_name == tool_name
        ).first()

        if not perm:
            reason = f"RBAC Denied: Role '{agent.role}' does not possess permission for tool '{tool_name}'."
            AuditService.log_event(
                db=db,
                agent_id=agent.id,
                agent_name=agent.name,
                agent_role=agent.role,
                tool_name=tool_name,
                parameters=parameters,
                decision="DENY",
                reason=reason,
                risk_level="HIGH",
                execution_status="BLOCKED"
            )
            return PolicyEvaluationResponse(
                decision="DENY",
                reason=reason,
                risk_level="HIGH",
                guardrail_flags=["RBAC_UNAUTHORIZED"]
            )

        # -------------------------------------------------------------
        # 6. SENSITIVITY & HUMAN APPROVAL THRESHOLDS
        # -------------------------------------------------------------
        risk_level = GuardrailsValidator.calculate_risk_level(tool_name, parameters)
        needs_approval = False
        approval_reason = ""

        # Check explicit permission flag
        if perm.requires_approval:
            needs_approval = True
            approval_reason = f"Tool '{tool_name}' is marked as requiring human verification by role policy."

        # Check critical sensitive tools
        elif tool_name in settings.SENSITIVE_TOOLS:
            needs_approval = True
            approval_reason = f"Tool '{tool_name}' is classified as a sensitive administrative action."

        # Check financial thresholds
        elif tool_name == "issue_refund":
            amount = float(parameters.get("amount", 0))
            if perm.max_amount and amount > perm.max_amount:
                reason = f"Limit Exceeded: Refund amount ${amount:,.2f} exceeds role authorization ceiling of ${perm.max_amount:,.2f}."
                AuditService.log_event(
                    db=db,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    tool_name=tool_name,
                    parameters=parameters,
                    decision="DENY",
                    reason=reason,
                    risk_level="HIGH",
                    execution_status="BLOCKED"
                )
                return PolicyEvaluationResponse(
                    decision="DENY",
                    reason=reason,
                    risk_level="HIGH",
                    guardrail_flags=["AMOUNT_LIMIT_EXCEEDED"]
                )
            elif amount > settings.REFUND_APPROVAL_THRESHOLD:
                needs_approval = True
                approval_reason = f"Refund amount ${amount:,.2f} exceeds auto-approval threshold (${settings.REFUND_APPROVAL_THRESHOLD:,.2f})."

        elif tool_name == "process_payment":
            amount = float(parameters.get("amount", 0))
            if perm.max_amount and amount > perm.max_amount:
                reason = f"Limit Exceeded: Payment amount ${amount:,.2f} exceeds role authorization ceiling of ${perm.max_amount:,.2f}."
                AuditService.log_event(
                    db=db,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    tool_name=tool_name,
                    parameters=parameters,
                    decision="DENY",
                    reason=reason,
                    risk_level="HIGH",
                    execution_status="BLOCKED"
                )
                return PolicyEvaluationResponse(
                    decision="DENY",
                    reason=reason,
                    risk_level="HIGH",
                    guardrail_flags=["AMOUNT_LIMIT_EXCEEDED"]
                )
            elif amount > settings.PAYMENT_APPROVAL_THRESHOLD:
                needs_approval = True
                approval_reason = f"Payment amount ${amount:,.2f} exceeds auto-approval threshold (${settings.PAYMENT_APPROVAL_THRESHOLD:,.2f})."

        # -------------------------------------------------------------
        # 7. ROUTE DECISION
        # -------------------------------------------------------------
        if needs_approval:
            approval_req = ApprovalService.create_request(
                db=db,
                agent_id=agent.id,
                agent_name=agent.name,
                agent_role=agent.role,
                tool_name=tool_name,
                parameters=parameters,
                reason=approval_reason
            )
            AuditService.log_event(
                db=db,
                agent_id=agent.id,
                agent_name=agent.name,
                agent_role=agent.role,
                tool_name=tool_name,
                parameters=parameters,
                decision="REQUIRE_APPROVAL",
                reason=approval_reason,
                risk_level=risk_level,
                execution_status="PENDING_APPROVAL"
            )
            return PolicyEvaluationResponse(
                decision="REQUIRE_APPROVAL",
                reason=approval_reason,
                risk_level=risk_level,
                guardrail_flags=guardrail_flags,
                approval_id=approval_req.id
            )

        # -------------------------------------------------------------
        # 8. ALLOW
        # -------------------------------------------------------------
        allow_reason = f"Action authorized. Agent '{agent.name}' has valid role '{agent.role}' and passed all safety guardrails."
        AuditService.log_event(
            db=db,
            agent_id=agent.id,
            agent_name=agent.name,
            agent_role=agent.role,
            tool_name=tool_name,
            parameters=parameters,
            decision="ALLOW",
            reason=allow_reason,
            risk_level=risk_level,
            execution_status="EXECUTED"
        )
        return PolicyEvaluationResponse(
            decision="ALLOW",
            reason=allow_reason,
            risk_level=risk_level,
            guardrail_flags=guardrail_flags,
            execution_preview=f"Executed tool '{tool_name}' successfully with parameters: {parameters}"
        )
