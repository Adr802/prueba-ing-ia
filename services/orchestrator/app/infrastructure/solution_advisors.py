import json
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.application.ports import SolutionAdvisor
from app.application.prompts import ADVISOR_SYSTEM_PROMPT
from app.domain.onboarding import Escalation, EscalationReason, OnboardingRequest

log = logging.getLogger(__name__)

_RULE_SOLUTIONS = {
    EscalationReason.LOW_IDENTITY_CONFIDENCE: "Solicitar validación biométrica o documento adicional y revisión del asesor.",
    EscalationReason.HIGH_RISK: "Enviar a Cumplimiento para debida diligencia reforzada antes de abrir el producto.",
    EscalationReason.UNSUPPORTED_PRODUCT: "Ofrecer un producto disponible equivalente y confirmar con el prospecto.",
    EscalationReason.AGENT_ERROR: "Reintentar el paso fallido; si persiste, completar la verificación manualmente.",
    EscalationReason.INCOMPLETE_FLOW: "Completar manualmente las verificaciones pendientes antes de decidir.",
}


class RuleBasedSolutionAdvisor:
    async def propose(self, request: OnboardingRequest, escalation: Escalation, results: dict) -> str:
        return _RULE_SOLUTIONS.get(escalation.reason, "Revisión manual completa por un asesor.")


class LlmSolutionAdvisor:
    """Proposes a solution with the LLM; falls back to fixed rules so an escalation always has one."""

    def __init__(self, llm: BaseChatModel, fallback: SolutionAdvisor):
        self._llm = llm
        self._fallback = fallback

    async def propose(self, request: OnboardingRequest, escalation: Escalation, results: dict) -> str:
        context = {
            "solicitud": request.model_dump(),
            "escalamiento": {"motivo": escalation.reason.value, "detalle": escalation.detail},
            "resultados_agentes": results,
        }
        try:
            reply = await self._llm.ainvoke(
                [SystemMessage(ADVISOR_SYSTEM_PROMPT), HumanMessage(json.dumps(context, ensure_ascii=False))]
            )
            if reply.content.strip():
                return reply.content.strip()
        except Exception:
            log.exception("LLM solution advisor failed; using rule-based fallback")
        return await self._fallback.propose(request, escalation, results)
