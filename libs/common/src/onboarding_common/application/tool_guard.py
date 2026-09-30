from onboarding_common.application.ports import ToolProvider, TracePublisher
from onboarding_common.domain.tool_policy import ToolNotAllowed, ToolPolicy
from onboarding_common.domain.trace import TraceEvent, TraceEventType


class ToolGuard:
    """Enforces the agent's allowlist on every tool listing and call, and traces both outcomes."""

    def __init__(self, policy: ToolPolicy, provider: ToolProvider, publisher: TracePublisher):
        self._policy = policy
        self._provider = provider
        self._publisher = publisher

    async def allowed_tools(self) -> list[dict]:
        tools = await self._provider.list_tools()
        return [t for t in tools if t["function"]["name"] in self._policy.allowed]

    async def call(self, name: str, args: dict, trace_id: str, step: int) -> dict:
        try:
            self._policy.check(name)
        except ToolNotAllowed as exc:
            await self._trace(trace_id, step, TraceEventType.TOOL_DENIED, {"tool": name, "args": args, "reason": str(exc)})
            raise
        result = await self._provider.call(name, args)
        await self._trace(trace_id, step, TraceEventType.TOOL_CALL, {"tool": name, "args": args, "result": result})
        return result

    async def _trace(self, trace_id: str, step: int, event: TraceEventType, payload: dict) -> None:
        await self._publisher.publish(
            TraceEvent(trace_id=trace_id, step=step, agent=self._policy.agent, event=event, payload=payload)
        )
