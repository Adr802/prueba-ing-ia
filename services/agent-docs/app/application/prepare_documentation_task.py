from onboarding_common.application.tool_agent import ToolAgent

from app.domain.documentation import REQUIRED_TOOL, DocumentationNotPrepared, DocumentationPackage

SYSTEM_PROMPT = """Eres el agente de documentación de apertura de productos de un banco.
Recibes un JSON con `product` y `client_data`. Debes llamar a la herramienta `prepare_documentation`
pasando `product` y `client_data` exactamente como los recibiste.
Luego responde en una frase en español indicando si el producto está disponible y cuántos documentos requiere.
No agregues documentos que la herramienta no devolvió."""


class PrepareDocumentationTask:
    def __init__(self, agent: ToolAgent):
        self._agent = agent

    async def handle(self, task: dict, trace_id: str, step: int) -> dict:
        request = {"product": task["product"], "client_data": task.get("client_data", {})}
        outcome = await self._agent.run(request, trace_id, step)
        raw = outcome["tool_results"].get(REQUIRED_TOOL)
        if raw is None:
            raise DocumentationNotPrepared(f"el agente no invocó '{REQUIRED_TOOL}'")
        return DocumentationPackage(**raw, analysis=outcome["analysis"]).model_dump()
