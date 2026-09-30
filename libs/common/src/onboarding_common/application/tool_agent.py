import json
from typing import Annotated, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from onboarding_common.application.tool_guard import ToolGuard
from onboarding_common.domain.tool_policy import ToolNotAllowed


class ToolAgentError(Exception):
    pass


class _State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    tool_results: dict
    iterations: int


class ToolAgent:
    """LLM + tools loop in LangGraph. Tool outputs are kept verbatim in `tool_results`,
    so business data never depends on the LLM re-typing numbers."""

    def __init__(self, llm: BaseChatModel, guard: ToolGuard, system_prompt: str, max_iterations: int = 3):
        self._llm = llm
        self._guard = guard
        self._system_prompt = system_prompt
        self._max_iterations = max_iterations

    async def run(self, task: dict, trace_id: str, step: int) -> dict:
        tools = await self._guard.allowed_tools()
        llm = self._llm.bind_tools(tools)

        async def think(state: _State):
            reply = await llm.ainvoke(state["messages"])
            return {"messages": [reply], "iterations": state["iterations"] + 1}

        async def act(state: _State):
            results = dict(state["tool_results"])
            messages = []
            for call in state["messages"][-1].tool_calls:
                try:
                    output = await self._guard.call(call["name"], call["args"], trace_id, step)
                    results[call["name"]] = output
                except ToolNotAllowed as exc:
                    output = {"error": str(exc)}
                messages.append(ToolMessage(content=json.dumps(output, ensure_ascii=False), tool_call_id=call["id"]))
            return {"messages": messages, "tool_results": results}

        def route(state: _State):
            wants_tools = bool(getattr(state["messages"][-1], "tool_calls", None))
            return "act" if wants_tools and state["iterations"] < self._max_iterations else END

        g = StateGraph(_State)
        g.add_node("think", think)
        g.add_node("act", act)
        g.add_edge(START, "think")
        g.add_conditional_edges("think", route)
        g.add_edge("act", "think")

        initial = {
            "messages": [SystemMessage(self._system_prompt), HumanMessage(json.dumps(task, ensure_ascii=False))],
            "tool_results": {},
            "iterations": 0,
        }
        try:
            final = await g.compile().ainvoke(initial)
        except Exception as exc:
            raise ToolAgentError(f"fallo del LLM/grafo: {exc}") from exc
        return {"tool_results": final["tool_results"], "analysis": final["messages"][-1].content}
