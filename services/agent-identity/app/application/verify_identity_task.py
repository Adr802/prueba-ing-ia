from onboarding_common.application.tool_agent import ToolAgent

from app.domain.identity import REQUIRED_TOOL, IdentityCheck, IdentityNotVerified

SYSTEM_PROMPT = """Eres el agente de verificación de identidad de un banco.
Recibes un JSON con `document_id`. Debes llamar a la herramienta `verify_identity` con ese document_id exacto.
Luego responde en una sola frase en español con tu análisis del resultado (verificado o no y el nivel de confianza).
No inventes datos: usa solo lo que devuelve la herramienta."""


class VerifyIdentityTask:
    def __init__(self, agent: ToolAgent):
        self._agent = agent

    async def handle(self, task: dict, trace_id: str, step: int) -> dict:
        outcome = await self._agent.run({"document_id": task["document_id"]}, trace_id, step)
        raw = outcome["tool_results"].get(REQUIRED_TOOL)
        if raw is None:
            raise IdentityNotVerified(f"el agente no invocó '{REQUIRED_TOOL}'")
        return IdentityCheck(**raw, analysis=outcome["analysis"]).model_dump()
