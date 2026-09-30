import json
from typing import TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.domain.reply import CustomerReply, ReplyRequest

SYSTEM_PROMPT = """Eres el agente de comunicación con clientes de un banco en su onboarding digital.
Recibes un JSON con el resultado de la solicitud y redactas el mensaje final para el prospecto.

Reglas:
- Español, tono cordial y profesional, máximo 4 frases. Dirígete al prospecto por su nombre.
- approved: confirma la aprobación del producto y enumera los documentos que debe firmar.
- escalated: indica que la solicitud está en revisión por un asesor y que será contactado pronto.
  NUNCA reveles el motivo interno (listas de riesgo, sanciones, baja confianza de identidad).
- rejected: indica que no fue posible validar su identidad en línea e invítalo a acercarse a una agencia.
- failed: discúlpate por el inconveniente e indica que un asesor lo contactará.
- No prometas plazos, montos ni condiciones que no estén en los datos.
Responde solo con el mensaje, sin encabezados ni formato adicional."""


class _State(TypedDict, total=False):
    request: ReplyRequest
    message: str


class ComposeReplyTask:
    def __init__(self, llm: BaseChatModel):
        async def write(state: _State):
            reply = await llm.ainvoke(
                [SystemMessage(SYSTEM_PROMPT), HumanMessage(state["request"].model_dump_json())]
            )
            return {"message": reply.content.strip()}

        g = StateGraph(_State)
        g.add_node("write", write)
        g.add_edge(START, "write")
        g.add_edge("write", END)
        self._graph = g.compile()

    async def handle(self, task: dict, trace_id: str, step: int) -> dict:
        state = await self._graph.ainvoke({"request": ReplyRequest(**task)})
        return CustomerReply(message=state["message"]).model_dump()
