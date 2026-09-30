from onboarding_common.application.tool_agent import ToolAgent

from app.domain.risk import REQUIRED_TOOL, RiskCheck, RiskNotAssessed

SYSTEM_PROMPT = """Eres el agente de cumplimiento (AML/KYC) de un banco.
Recibes un JSON con `name` y `document_id` de un prospecto. Debes llamar a la herramienta `check_risk_lists`
con esos valores exactos para consultar listas restrictivas (OFAC, PEP, listas locales).
Luego responde en una o dos frases en español con tu análisis: nivel de riesgo y en qué listas hubo coincidencias.
No inventes coincidencias: usa solo lo que devuelve la herramienta."""


class CheckRiskTask:
    def __init__(self, agent: ToolAgent):
        self._agent = agent

    async def handle(self, task: dict, trace_id: str, step: int) -> dict:
        request = {"name": task["name"], "document_id": task["document_id"]}
        outcome = await self._agent.run(request, trace_id, step)
        raw = outcome["tool_results"].get(REQUIRED_TOOL)
        if raw is None:
            raise RiskNotAssessed(f"el agente no invocó '{REQUIRED_TOOL}'")
        return RiskCheck(**raw, analysis=outcome["analysis"]).model_dump()
