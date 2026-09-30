from enum import StrEnum

from pydantic import BaseModel, Field

MIN_IDENTITY_CONFIDENCE = 0.8
MAX_STEPS = 10
GLOBAL_TIMEOUT_SECONDS = 30.0


class OnboardingRequest(BaseModel):
    prospect_name: str = Field(min_length=1)
    document_id: str = Field(pattern=r"^\d{10}$")
    product: str = Field(min_length=1)


class OnboardingStatus(StrEnum):
    APPROVED = "approved"
    ESCALATED = "escalated"
    REJECTED = "rejected"
    FAILED = "failed"


class EscalationReason(StrEnum):
    LOW_IDENTITY_CONFIDENCE = "low_identity_confidence"
    HIGH_RISK = "high_risk"
    UNSUPPORTED_PRODUCT = "unsupported_product"
    AGENT_ERROR = "agent_error"
    INCOMPLETE_FLOW = "incomplete_flow"
    MAX_STEPS_EXCEEDED = "max_steps_exceeded"
    TIMEOUT = "timeout"


class Escalation(BaseModel):
    reason: EscalationReason
    detail: str
    proposed_solution: str = ""


class Decision(BaseModel):
    status: OnboardingStatus | None = None  # None means: continue the flow
    escalation: Escalation | None = None
    notes: list[str] = Field(default_factory=list)


class OnboardingResult(BaseModel):
    trace_id: str
    status: OnboardingStatus
    escalation: Escalation | None
    results: dict
    customer_message: str
    steps: int


class MaxStepsExceeded(Exception):
    pass


def evaluate_verifications(identity: dict, risk: dict) -> Decision:
    """Business rules R4, R5, R9 and the escalation thresholds from the spec."""
    for name, result in (("identity", identity), ("risk", risk)):
        if "error" in result:
            return _escalate(EscalationReason.AGENT_ERROR, f"{name}: {result['error']}")

    if identity["confidence"] < MIN_IDENTITY_CONFIDENCE:
        return _escalate(
            EscalationReason.LOW_IDENTITY_CONFIDENCE,
            f"confianza de identidad {identity['confidence']} < {MIN_IDENTITY_CONFIDENCE}",
        )
    if risk["risk_level"] == "high":
        return _escalate(EscalationReason.HIGH_RISK, f"coincidencias: {risk['matches']}")
    if not identity["verified"]:
        return Decision(status=OnboardingStatus.REJECTED, notes=["identidad no verificada con confianza alta"])

    notes = [f"riesgo medio: {risk['matches']}"] if risk["risk_level"] == "medium" else []
    return Decision(notes=notes)


def evaluate_documentation(documentation: dict) -> Decision:
    if "error" in documentation:
        return _escalate(EscalationReason.AGENT_ERROR, f"documentation: {documentation['error']}")
    if not documentation["supported"]:
        return _escalate(EscalationReason.UNSUPPORTED_PRODUCT, f"producto '{documentation['product']}' no disponible")
    return Decision(status=OnboardingStatus.APPROVED)


def escalate(reason: EscalationReason, detail: str) -> Decision:
    return _escalate(reason, detail)


def _escalate(reason: EscalationReason, detail: str) -> Decision:
    return Decision(status=OnboardingStatus.ESCALATED, escalation=Escalation(reason=reason, detail=detail))
