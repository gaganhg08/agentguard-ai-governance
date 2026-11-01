import traceback
from typing import Any, Optional
from sqlalchemy.orm import Session
from backend.config import settings
from backend.models import Agent, Permission, PolicyRule
from backend.guardrails import GuardrailsValidator, REGISTERED_TOOLS
from backend.audit_service import AuditService
from backend.approval_service import ApprovalService
from backend.schemas import PolicyEvaluationResponse

class PolicyEngine:
    """
    AgentGuard Central Authorization & Policy Enforcement Gateway.
    
    Evaluates:
    1. Agent Identity
    2. Agent Active Lifecycle Status
    3. Action & Tool Registration
    4. Guardrails & Prompt Injection Threat Filters
    5. Parameter Boundaries & Resource Restrictions
    6. Role-Based Access Control (RBAC)
    7. Dynamic Sensitivity & Human Approval Policies
    
    Security Guarantees:
    - Default-Deny when evaluation fails or policy is missing.
    - Zero trust for autonomous LLM agents.
    - Full cryptographic audit logging for every decision.
    """

    @classmethod
    def evaluate(
        cls,
        db: Session,
        agent_id: str,
        tool_name: str,
        parameters: dict[str, Any] = None,
        resource: Optional[str] = None,
        context: Optional[dict[str, Any]] = None
    ) -> PolicyEvaluationResponse:
        parameters = parameters or {}
        context = context or {}
        resource_target = resource.strip() if resource and resource.strip() else "System / General"
        guardrail_flags: list[str] = []
        evaluation_trace: list[dict[str, str]] = []

        try:
            # -------------------------------------------------------------
            # 1. AGENT IDENTITY VALIDATION
            # -------------------------------------------------------------
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                reason = f"Identity Denied: Agent ID '{agent_id}' is unknown or not registered in security directory."
                evaluation_trace.append({"step": "Identity Verification", "status": "FAIL", "detail": reason})
                AuditService.log_event(
                    db=db,
                    agent_id=agent_id,
                    agent_name="Unknown Agent",
                    agent_role="Unknown",
                    tool_name=tool_name,
                    parameters=parameters,
                    decision="DENY",
                    reason=reason,
                    resource=resource_target,
                    risk_level="HIGH",
                    execution_status="BLOCKED"
                )
                return PolicyEvaluationResponse(
                    decision="DENY",
                    agent_id=agent_id,
                    agent_name="Unknown Agent",
                    agent_role="Unknown",
                    requested_action=tool_name,
                    target_resource=resource_target,
                    applicable_policy="Identity Verification Policy",
                    reason=reason,
                    risk_level="HIGH",
                    requires_human_approval=False,
                    guardrail_flags=["UNKNOWN_AGENT"],
                    evaluation_trace=evaluation_trace
                )

            evaluation_trace.append({
                "step": "Identity Verification",
                "status": "PASS",
                "detail": f"Verified agent identity '{agent.name}' ({agent.id}) with role '{agent.role}'."
            })

            # -------------------------------------------------------------
            # 2. AGENT ACTIVE LIFECYCLE STATUS
            # -------------------------------------------------------------
            if not agent.is_active:
                reason = f"Access Denied: Agent '{agent.name}' ({agent.id}) is DEACTIVATED."
                evaluation_trace.append({"step": "Lifecycle Check", "status": "FAIL", "detail": reason})
                AuditService.log_event(
                    db=db,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    tool_name=tool_name,
                    parameters=parameters,
                    decision="DENY",
                    reason=reason,
                    resource=resource_target,
                    risk_level="MEDIUM",
                    execution_status="BLOCKED"
                )
                return PolicyEvaluationResponse(
                    decision="DENY",
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    requested_action=tool_name,
                    target_resource=resource_target,
                    applicable_policy="Agent Lifecycle Policy",
                    reason=reason,
                    risk_level="MEDIUM",
                    requires_human_approval=False,
                    guardrail_flags=["AGENT_INACTIVE"],
                    evaluation_trace=evaluation_trace
                )

            evaluation_trace.append({
                "step": "Lifecycle Check",
                "status": "PASS",
                "detail": "Agent is in ACTIVE operational status."
            })

            # -------------------------------------------------------------
            # 3. TOOL / PERMISSION CATALOG VALIDATION
            # -------------------------------------------------------------
            is_registered, tool_err = GuardrailsValidator.check_tool_registered(tool_name)
            if not is_registered:
                reason = f"Security Guardrail: {tool_err}"
                evaluation_trace.append({"step": "Catalog Verification", "status": "FAIL", "detail": reason})
                AuditService.log_event(
                    db=db,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    tool_name=tool_name,
                    parameters=parameters,
                    decision="DENY",
                    reason=reason,
                    resource=resource_target,
                    risk_level="HIGH",
                    execution_status="BLOCKED"
                )
                return PolicyEvaluationResponse(
                    decision="DENY",
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    requested_action=tool_name,
                    target_resource=resource_target,
                    applicable_policy="Tool Registration Policy",
                    reason=reason,
                    risk_level="HIGH",
                    requires_human_approval=False,
                    guardrail_flags=["UNREGISTERED_TOOL"],
                    evaluation_trace=evaluation_trace
                )

            evaluation_trace.append({
                "step": "Catalog Verification",
                "status": "PASS",
                "detail": f"Tool '{tool_name}' verified in enterprise tool catalog."
            })

            # -------------------------------------------------------------
            # 4. GUARDRAILS: PROMPT INJECTION & THREAT INSPECTION
            # -------------------------------------------------------------
            injection_signals = GuardrailsValidator.detect_prompt_injection(parameters)
            if injection_signals:
                guardrail_flags.extend(injection_signals)
                reason = f"Security Violation: Potential prompt injection or malicious pattern blocked: {'; '.join(injection_signals)}"
                evaluation_trace.append({"step": "Threat Guardrails", "status": "FAIL", "detail": reason})
                AuditService.log_event(
                    db=db,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    tool_name=tool_name,
                    parameters=parameters,
                    decision="DENY",
                    reason=reason,
                    resource=resource_target,
                    risk_level="CRITICAL",
                    guardrail_flags=guardrail_flags,
                    execution_status="BLOCKED"
                )
                return PolicyEvaluationResponse(
                    decision="DENY",
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    requested_action=tool_name,
                    target_resource=resource_target,
                    applicable_policy="Prompt Injection & Metacharacter Defense",
                    reason=reason,
                    risk_level="CRITICAL",
                    requires_human_approval=False,
                    guardrail_flags=guardrail_flags,
                    evaluation_trace=evaluation_trace
                )

            evaluation_trace.append({
                "step": "Threat Guardrails",
                "status": "PASS",
                "detail": "Zero prompt injection, shell metacharacter, or SQL injection signatures detected."
            })

            # -------------------------------------------------------------
            # 5. RESOURCE RESTRICTIONS & PARAMETER VALIDATION
            # -------------------------------------------------------------
            is_valid_params, param_err = GuardrailsValidator.validate_tool_parameters(tool_name, parameters)
            if not is_valid_params:
                reason = f"Validation Failed: {param_err}"
                evaluation_trace.append({"step": "Parameter Validation", "status": "FAIL", "detail": reason})
                AuditService.log_event(
                    db=db,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    tool_name=tool_name,
                    parameters=parameters,
                    decision="DENY",
                    reason=reason,
                    resource=resource_target,
                    risk_level="MEDIUM",
                    execution_status="BLOCKED"
                )
                return PolicyEvaluationResponse(
                    decision="DENY",
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    requested_action=tool_name,
                    target_resource=resource_target,
                    applicable_policy="Parameter Validation Policy",
                    reason=reason,
                    risk_level="MEDIUM",
                    requires_human_approval=False,
                    guardrail_flags=["INVALID_PARAMETERS"],
                    evaluation_trace=evaluation_trace
                )

            # Check resource restrictions if target is production/restricted
            if "prod" in resource_target.lower() and agent.role == "Customer Support":
                reason = f"Resource Restriction: Role '{agent.role}' cannot directly target production resource '{resource_target}'."
                evaluation_trace.append({"step": "Resource Boundary Check", "status": "FAIL", "detail": reason})
                AuditService.log_event(
                    db=db,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    tool_name=tool_name,
                    parameters=parameters,
                    decision="DENY",
                    reason=reason,
                    resource=resource_target,
                    risk_level="HIGH",
                    execution_status="BLOCKED"
                )
                return PolicyEvaluationResponse(
                    decision="DENY",
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    requested_action=tool_name,
                    target_resource=resource_target,
                    applicable_policy="Resource Isolation Policy",
                    reason=reason,
                    risk_level="HIGH",
                    requires_human_approval=False,
                    guardrail_flags=["RESOURCE_RESTRICTION_EXCEEDED"],
                    evaluation_trace=evaluation_trace
                )

            evaluation_trace.append({
                "step": "Parameter Validation",
                "status": "PASS",
                "detail": f"Parameters and target resource '{resource_target}' are within bounds."
            })

            # -------------------------------------------------------------
            # 6. ROLE-BASED ACCESS CONTROL (RBAC) & LEAST PRIVILEGE
            # -------------------------------------------------------------
            perm = db.query(Permission).filter(
                Permission.role == agent.role,
                Permission.tool_name == tool_name
            ).first()

            if not perm:
                reason = f"RBAC Denied: Role '{agent.role}' does not possess permission for tool '{tool_name}'."
                evaluation_trace.append({"step": "RBAC Check", "status": "FAIL", "detail": reason})
                AuditService.log_event(
                    db=db,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    tool_name=tool_name,
                    parameters=parameters,
                    decision="DENY",
                    reason=reason,
                    resource=resource_target,
                    risk_level="HIGH",
                    execution_status="BLOCKED"
                )
                return PolicyEvaluationResponse(
                    decision="DENY",
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    requested_action=tool_name,
                    target_resource=resource_target,
                    applicable_policy=f"RBAC Policy: Role '{agent.role}'",
                    reason=reason,
                    risk_level="HIGH",
                    requires_human_approval=False,
                    guardrail_flags=["RBAC_UNAUTHORIZED"],
                    evaluation_trace=evaluation_trace
                )

            evaluation_trace.append({
                "step": "RBAC Check",
                "status": "PASS",
                "detail": f"Role '{agent.role}' explicitly holds authorization for '{tool_name}'."
            })

            # -------------------------------------------------------------
            # 7. SENSITIVITY, DYNAMIC POLICIES & APPROVAL GATES
            # -------------------------------------------------------------
            risk_level = GuardrailsValidator.calculate_risk_level(tool_name, parameters)
            needs_approval = False
            approval_reason = ""
            applicable_policy = f"RBAC Policy: Role '{agent.role}'"

            # Check explicit permission approval requirement
            if perm.requires_approval:
                needs_approval = True
                approval_reason = f"Tool '{tool_name}' is marked as requiring human verification by role policy."
                applicable_policy = "Mandatory Role Verification Policy"

            # Check critical sensitive tools
            elif tool_name in settings.SENSITIVE_TOOLS:
                needs_approval = True
                approval_reason = f"Tool '{tool_name}' is classified as a sensitive administrative action."
                applicable_policy = "Critical Infrastructure Policy"

            # Financial limit ceiling checks
            elif tool_name == "issue_refund":
                amount = float(parameters.get("amount", 0))
                if perm.max_amount and amount > perm.max_amount:
                    reason = f"Limit Exceeded: Refund amount ${amount:,.2f} exceeds role authorization ceiling of ${perm.max_amount:,.2f}."
                    evaluation_trace.append({"step": "Monetary Bounds", "status": "FAIL", "detail": reason})
                    AuditService.log_event(
                        db=db,
                        agent_id=agent.id,
                        agent_name=agent.name,
                        agent_role=agent.role,
                        tool_name=tool_name,
                        parameters=parameters,
                        decision="DENY",
                        reason=reason,
                        resource=resource_target,
                        risk_level="HIGH",
                        execution_status="BLOCKED"
                    )
                    return PolicyEvaluationResponse(
                        decision="DENY",
                        agent_id=agent.id,
                        agent_name=agent.name,
                        agent_role=agent.role,
                        requested_action=tool_name,
                        target_resource=resource_target,
                        applicable_policy="Financial Spending Ceiling Policy",
                        reason=reason,
                        risk_level="HIGH",
                        requires_human_approval=False,
                        guardrail_flags=["AMOUNT_LIMIT_EXCEEDED"],
                        evaluation_trace=evaluation_trace
                    )
                elif amount > settings.REFUND_APPROVAL_THRESHOLD:
                    needs_approval = True
                    approval_reason = f"Refund amount ${amount:,.2f} exceeds auto-approval threshold (${settings.REFUND_APPROVAL_THRESHOLD:,.2f})."
                    applicable_policy = "High-Value Transaction Policy"

            elif tool_name == "process_payment":
                amount = float(parameters.get("amount", 0))
                if perm.max_amount and amount > perm.max_amount:
                    reason = f"Limit Exceeded: Payment amount ${amount:,.2f} exceeds role authorization ceiling of ${perm.max_amount:,.2f}."
                    evaluation_trace.append({"step": "Monetary Bounds", "status": "FAIL", "detail": reason})
                    AuditService.log_event(
                        db=db,
                        agent_id=agent.id,
                        agent_name=agent.name,
                        agent_role=agent.role,
                        tool_name=tool_name,
                        parameters=parameters,
                        decision="DENY",
                        reason=reason,
                        resource=resource_target,
                        risk_level="HIGH",
                        execution_status="BLOCKED"
                    )
                    return PolicyEvaluationResponse(
                        decision="DENY",
                        agent_id=agent.id,
                        agent_name=agent.name,
                        agent_role=agent.role,
                        requested_action=tool_name,
                        target_resource=resource_target,
                        applicable_policy="Corporate Disbursement Ceiling Policy",
                        reason=reason,
                        risk_level="HIGH",
                        requires_human_approval=False,
                        guardrail_flags=["AMOUNT_LIMIT_EXCEEDED"],
                        evaluation_trace=evaluation_trace
                    )
                elif amount > settings.PAYMENT_APPROVAL_THRESHOLD:
                    needs_approval = True
                    approval_reason = f"Payment amount ${amount:,.2f} exceeds auto-approval threshold (${settings.PAYMENT_APPROVAL_THRESHOLD:,.2f})."
                    applicable_policy = "High-Value Transaction Policy"

            # Check dynamic database policy rules
            active_rules = db.query(PolicyRule).filter(
                PolicyRule.is_active == True,
                (PolicyRule.target_tool == tool_name) | (PolicyRule.target_tool == "*")
            ).order_by(PolicyRule.priority.asc()).all()

            for rule in active_rules:
                if rule.action == "REQUIRE_APPROVAL" and not needs_approval:
                    if rule.condition_type == "amount_threshold":
                        try:
                            rule_limit = float(rule.condition_value)
                            val = float(parameters.get("amount", 0))
                            if val > rule_limit:
                                needs_approval = True
                                approval_reason = f"Policy Rule '{rule.name}' triggered: Amount ${val:,.2f} exceeds rule limit of ${rule_limit:,.2f}."
                                applicable_policy = f"Custom Security Policy: {rule.name}"
                        except Exception:
                            pass
                    elif rule.condition_type == "role_whitelist":
                        if agent.role in [r.strip() for r in rule.condition_value.split(",")]:
                            needs_approval = True
                            approval_reason = f"Policy Rule '{rule.name}' mandates human authorization for role '{agent.role}'."
                            applicable_policy = f"Custom Security Policy: {rule.name}"

            # -------------------------------------------------------------
            # 8. OUTCOME: REQUIRE_APPROVAL
            # -------------------------------------------------------------
            if needs_approval:
                approval_req = ApprovalService.create_request(
                    db=db,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    tool_name=tool_name,
                    parameters=parameters,
                    reason=approval_reason,
                    resource=resource_target
                )
                evaluation_trace.append({
                    "step": "Approval Gate",
                    "status": "PAUSED",
                    "detail": f"Action paused: {approval_reason} (Request ID: {approval_req.id})."
                })
                AuditService.log_event(
                    db=db,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    tool_name=tool_name,
                    parameters=parameters,
                    decision="REQUIRE_APPROVAL",
                    reason=approval_reason,
                    resource=resource_target,
                    risk_level=risk_level,
                    execution_status="PENDING_APPROVAL"
                )
                return PolicyEvaluationResponse(
                    decision="REQUIRE_APPROVAL",
                    agent_id=agent.id,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    requested_action=tool_name,
                    target_resource=resource_target,
                    applicable_policy=applicable_policy,
                    reason=approval_reason,
                    risk_level=risk_level,
                    requires_human_approval=True,
                    guardrail_flags=guardrail_flags,
                    approval_id=approval_req.id,
                    evaluation_trace=evaluation_trace
                )

            # -------------------------------------------------------------
            # 9. OUTCOME: ALLOW
            # -------------------------------------------------------------
            allow_reason = f"Action authorized. Agent '{agent.name}' has valid role '{agent.role}' and passed all safety guardrails."
            evaluation_trace.append({
                "step": "Final Verdict",
                "status": "PASS",
                "detail": "All security guardrails, bounds, and RBAC policies satisfied."
            })
            AuditService.log_event(
                db=db,
                agent_id=agent.id,
                agent_name=agent.name,
                agent_role=agent.role,
                tool_name=tool_name,
                parameters=parameters,
                decision="ALLOW",
                reason=allow_reason,
                resource=resource_target,
                risk_level=risk_level,
                execution_status="EXECUTED"
            )
            return PolicyEvaluationResponse(
                decision="ALLOW",
                agent_id=agent.id,
                agent_name=agent.name,
                agent_role=agent.role,
                requested_action=tool_name,
                target_resource=resource_target,
                applicable_policy=applicable_policy,
                reason=allow_reason,
                risk_level=risk_level,
                requires_human_approval=False,
                guardrail_flags=guardrail_flags,
                execution_preview=f"Executed tool '{tool_name}' successfully on resource '{resource_target}' with parameters: {parameters}",
                evaluation_trace=evaluation_trace
            )

        except Exception as ex:
            # -------------------------------------------------------------
            # DEFAULT-DENY FALLBACK ON EVALUATION ERROR
            # -------------------------------------------------------------
            fallback_reason = f"Policy Evaluation Exception: {str(ex)}. Default-Deny enforced for platform security."
            evaluation_trace.append({"step": "Exception Handling", "status": "FAIL", "detail": fallback_reason})
            try:
                AuditService.log_event(
                    db=db,
                    agent_id=agent_id,
                    agent_name="Exception Handler",
                    agent_role="Unknown",
                    tool_name=tool_name,
                    parameters=parameters,
                    decision="DENY",
                    reason=fallback_reason,
                    resource=resource_target,
                    risk_level="CRITICAL",
                    execution_status="BLOCKED"
                )
            except Exception:
                pass

            return PolicyEvaluationResponse(
                decision="DENY",
                agent_id=agent_id,
                agent_name="System Gateway",
                agent_role="Gateway",
                requested_action=tool_name,
                target_resource=resource_target,
                applicable_policy="Fail-Safe Default-Deny Policy",
                reason="Default to DENY: Policy evaluation encountered an unhandled exception or missing configuration.",
                risk_level="CRITICAL",
                requires_human_approval=False,
                guardrail_flags=["EVALUATION_ERROR_DEFAULT_DENY"],
                evaluation_trace=evaluation_trace
            )
