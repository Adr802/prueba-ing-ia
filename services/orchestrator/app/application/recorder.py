from onboarding_common.application.ports import TracePublisher
from onboarding_common.domain.trace import TraceEvent, TraceEventType

from app.domain.onboarding import MaxStepsExceeded


class RunRecorder:
    """Per-request step counter and trace emitter. Enforces max_steps."""

    def __init__(self, trace_id: str, publisher: TracePublisher, max_steps: int):
        self.trace_id = trace_id
        self._publisher = publisher
        self._max_steps = max_steps
        self.steps = 0

    async def step(self, agent: str, payload: dict | None = None) -> None:
        if self.steps >= self._max_steps:
            raise MaxStepsExceeded(f"se alcanzó max_steps={self._max_steps} antes de '{agent}'")
        self.steps += 1
        await self.emit(agent, TraceEventType.STEP, payload or {})

    async def emit(self, agent: str, event: TraceEventType, payload: dict) -> None:
        await self._publisher.publish(
            TraceEvent(trace_id=self.trace_id, step=self.steps, agent=agent, event=event, payload=payload)
        )
