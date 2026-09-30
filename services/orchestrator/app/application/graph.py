import asyncio
import json
from typing import Annotated, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from onboarding_common.domain.tool_policy import ToolNotAllowed, ToolPolicy
from onboarding_common.domain.trace import TraceEventType

from app.application.ports import AgentError, AgentGateway, SolutionAdvisor
from app.application.prompts import ROUTER_SYSTEM_PROMPT
from app.application.recorder import RunRecorder
from app.domain.onboarding import (
    MAX_STEPS,
    Decision,
    EscalationReason,
    MaxStepsExceeded,
    OnboardingRequest,
    OnboardingStatus,
    escalate,
    evaluate_documentation,
    evaluate_verifications,
)


def _tool(name: str, description: str) -> dict:
    return {"type": "function", "function": {"name": name, "description": description,
                                             "parameters": {"type": "object", "properties": {}}}}


AGENT_TOOLS = [
    _tool("verificar_identidad", "Invoca al agente de identidad para validar el documento del prospecto."),
    _tool("consultar_listas_riesgo", "Invoca al agente de cumplimiento para consultar listas de riesgo."),
    _tool("preparar_documentacion", "Invoca al agente de documentación para el producto solicitado."),
    _tool("responder_cliente", "Invoca al agente de comunicación para redactar el mensaje final."),
]
TOOL_TO_AGENT = {
    "verificar_identidad": "identity",
    "consultar_listas_riesgo": "risk",
    "preparar_documentacion": "documentation",
    "responder_cliente": "response",
}


class OrchestratorState(TypedDict, total=False):
    request: OnboardingRequest
    messages: Annotated[list[AnyMessage], add_messages]
    results: dict
    decision: Decision | None
    customer_message: str | None
    turns: int
    llm_error: str | None


def _recorder(config: RunnableConfig) -> RunRecorder:
    return config["configurable"]["recorder"]


def build_graph(llm: BaseChatModel, agents: AgentGateway, advisor: SolutionAdvisor, policy: ToolPolicy):
    router = llm.bind_tools(AGENT_TOOLS)

    def payload_for(agent: str, state: OrchestratorState, decision: Decision | None) -> dict:
        # Agent inputs always come from the validated request and prior results, never from LLM arguments.
        req, results = state["request"], state["results"]
        if agent == "identity":
            return {"document_id": req.document_id}
        if agent == "risk":
            return {"name": req.prospect_name, "document_id": req.document_id}
        if agent == "documentation":
            client = {"name": req.prospect_name, "document_id": req.document_id, "identity": results.get("identity")}
            return {"product": req.product, "client_data": client}
        return {
            "prospect_name": req.prospect_name,
            "product": req.product,
            "status": decision.status.value,
            "documents": (results.get("documentation") or {}).get("documents", []),
            "escalation_reason": decision.escalation.reason.value if decision.escalation else None,
        }

    def precondition(agent: str, state: OrchestratorState, decision: Decision | None) -> str | None:
        results = state["results"]
        if agent in results or (agent == "response" and state.get("customer_message")):
            return "ya fue ejecutado"
        if agent == "documentation" and (decision is None or decision.status is not None):
            return "requiere identidad y riesgo completos y sin escalamiento ni rechazo"
        if agent == "response" and (decision is None or decision.status is None):
            return "requiere un veredicto final (approved, escalated o rejected)"
        return None

    async def propose(state: OrchestratorState, decision: Decision, rec: RunRecorder) -> Decision:
        await rec.step("orchestrator", {"action": "propose_solution"})
        decision = decision.model_copy(deep=True)
        decision.escalation.proposed_solution = await advisor.propose(state["request"], decision.escalation, state["results"])
        await rec.emit("orchestrator", TraceEventType.ESCALATION,
                       {"handoff": "asesor", **decision.escalation.model_dump(mode="json")})
        return decision

    async def think(state: OrchestratorState, config: RunnableConfig):
        rec = _recorder(config)
        if state["turns"] >= MAX_STEPS:
            raise MaxStepsExceeded(f"el enrutador superó {MAX_STEPS} turnos")
        try:
            reply = await router.ainvoke(state["messages"])
        except Exception as exc:
            await rec.emit("orchestrator", TraceEventType.ERROR, {"llm_error": str(exc)})
            return {"llm_error": str(exc), "turns": state["turns"] + 1}
        chosen = [c["name"] for c in reply.tool_calls]
        await rec.emit("orchestrator", TraceEventType.DECISION, {"router_turn": state["turns"] + 1, "tools": chosen})
        return {"messages": [reply], "turns": state["turns"] + 1}

    async def act(state: OrchestratorState, config: RunnableConfig):
        rec = _recorder(config)
        results = dict(state["results"])
        decision = state.get("decision")
        customer_message = state.get("customer_message")
        view = {**state, "results": results}

        async def run(call: dict) -> ToolMessage:
            nonlocal customer_message
            name, agent = call["name"], TOOL_TO_AGENT.get(call["name"], call["name"])
            try:
                policy.check(name)
            except ToolNotAllowed as exc:
                await rec.emit("orchestrator", TraceEventType.TOOL_DENIED, {"tool": name, "reason": str(exc)})
                return ToolMessage(json.dumps({"error": str(exc)}, ensure_ascii=False), tool_call_id=call["id"])
            blocked = precondition(agent, {**view, "customer_message": customer_message}, decision)
            if blocked:
                await rec.emit("orchestrator", TraceEventType.DECISION, {"blocked": name, "reason": blocked})
                return ToolMessage(json.dumps({"bloqueado": blocked}, ensure_ascii=False), tool_call_id=call["id"])

            payload = payload_for(agent, view, decision)
            await rec.step(agent, {"tool": name, "input": payload})
            try:
                output = await agents.invoke(agent, payload, rec.trace_id, rec.steps)
                await rec.emit(agent, TraceEventType.TOOL_CALL, {"tool": name, "result": output})
            except AgentError as exc:
                output = {"error": str(exc)}
                await rec.emit(agent, TraceEventType.ERROR, output)
            if agent == "response":
                customer_message = output.get("message")
            else:
                results[agent] = output
            return ToolMessage(json.dumps(output, ensure_ascii=False), tool_call_id=call["id"])

        tool_messages = list(await asyncio.gather(*(run(c) for c in state["messages"][-1].tool_calls)))

        if decision is None and "identity" in results and "risk" in results:
            decision = evaluate_verifications(results["identity"], results["risk"])
            await rec.emit("orchestrator", TraceEventType.DECISION, decision.model_dump(mode="json"))
        if decision is not None and decision.status is None and "documentation" in results:
            notes = decision.notes
            decision = evaluate_documentation(results["documentation"])
            decision.notes = notes + decision.notes
            await rec.emit("orchestrator", TraceEventType.DECISION, decision.model_dump(mode="json"))
        if decision and decision.escalation and not decision.escalation.proposed_solution:
            decision = await propose({**state, "results": results}, decision, rec)

        status = "en_curso" if decision is None or decision.status is None else decision.status.value
        next_action = (
            "finalizar respondiendo FIN" if customer_message
            else "responder_cliente" if status != "en_curso"
            else "preparar_documentacion" if decision is not None
            else "completar verificar_identidad y consultar_listas_riesgo"
        )
        note = HumanMessage(f"Estado del orquestador: {json.dumps({'estado': status, 'siguiente_accion': next_action})}")
        return {"messages": tool_messages + [note], "results": results, "decision": decision,
                "customer_message": customer_message}

    async def finalize(state: OrchestratorState, config: RunnableConfig):
        rec = _recorder(config)
        decision = state.get("decision")
        if decision is None or decision.status is None:
            reason = EscalationReason.AGENT_ERROR if state.get("llm_error") else EscalationReason.INCOMPLETE_FLOW
            detail = f"orquestador LLM: {state['llm_error']}" if state.get("llm_error") else "el enrutador terminó sin completar el flujo"
            decision = escalate(reason, detail)
            await rec.emit("orchestrator", TraceEventType.DECISION, decision.model_dump(mode="json"))
        if decision.escalation and not decision.escalation.proposed_solution:
            decision = await propose(state, decision, rec)

        message = state.get("customer_message")
        if not message:
            # Guarantee the customer always gets an answer, even if the router skipped the response agent.
            payload = payload_for("response", state, decision)
            await rec.step("response", {"tool": "responder_cliente", "input": payload, "forced": True})
            try:
                message = (await agents.invoke("response", payload, rec.trace_id, rec.steps)).get("message")
            except AgentError as exc:
                await rec.emit("response", TraceEventType.ERROR, {"error": str(exc)})
        return {"decision": decision, "customer_message": message or fallback_message(decision.status)}

    def after_think(state: OrchestratorState) -> str:
        last = state["messages"][-1]
        if state.get("llm_error") or not getattr(last, "tool_calls", None):
            return "finalize"
        return "act"

    g = StateGraph(OrchestratorState)
    g.add_node("think", think)
    g.add_node("act", act)
    g.add_node("finalize", finalize)
    g.add_edge(START, "think")
    g.add_conditional_edges("think", after_think, ["act", "finalize"])
    g.add_edge("act", "think")
    g.add_edge("finalize", END)
    return g.compile()


def initial_state(request: OnboardingRequest) -> OrchestratorState:
    return {
        "request": request,
        "messages": [
            SystemMessage(ROUTER_SYSTEM_PROMPT),
            HumanMessage(f"Nueva solicitud de onboarding: {request.model_dump_json()}"),
        ],
        "results": {},
        "decision": None,
        "customer_message": None,
        "turns": 0,
        "llm_error": None,
    }


def fallback_message(status: OnboardingStatus) -> str:
    return {
        OnboardingStatus.APPROVED: "Tu solicitud fue aprobada. Te enviaremos los documentos para firmar.",
        OnboardingStatus.ESCALATED: "Tu solicitud está en revisión por un asesor. Te contactaremos pronto.",
        OnboardingStatus.REJECTED: "No pudimos validar tu identidad. Acércate a una agencia para continuar.",
    }.get(status, "Tuvimos un inconveniente procesando tu solicitud. Un asesor te contactará.")
