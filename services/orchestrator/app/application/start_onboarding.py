import asyncio
import uuid

from onboarding_common.application.ports import TracePublisher
from onboarding_common.domain.trace import TraceEventType

from app.application.graph import fallback_message, initial_state
from app.application.recorder import RunRecorder
from app.domain.onboarding import (
    Escalation,
    EscalationReason,
    MaxStepsExceeded,
    OnboardingRequest,
    OnboardingResult,
    OnboardingStatus,
)


class StartOnboarding:
    def __init__(self, graph, publisher: TracePublisher, max_steps: int, timeout_seconds: float):
        self._graph = graph
        self._publisher = publisher
        self._max_steps = max_steps
        self._timeout = timeout_seconds

    async def execute(self, request: OnboardingRequest) -> OnboardingResult:
        rec = RunRecorder(str(uuid.uuid4()), self._publisher, self._max_steps)
        await rec.emit("orchestrator", TraceEventType.STEP, {"action": "received", "request": request.model_dump()})
        config = {"configurable": {"recorder": rec}, "recursion_limit": 4 * self._max_steps}
        try:
            state = await asyncio.wait_for(self._graph.ainvoke(initial_state(request), config), self._timeout)
        except TimeoutError:
            return await self._abort(rec, EscalationReason.TIMEOUT, f"superó el timeout global de {self._timeout}s")
        except MaxStepsExceeded as exc:
            return await self._abort(rec, EscalationReason.MAX_STEPS_EXCEEDED, str(exc))

        decision = state["decision"]
        result = OnboardingResult(
            trace_id=rec.trace_id,
            status=decision.status,
            escalation=decision.escalation,
            results={k: state["results"].get(k) for k in ("identity", "risk", "documentation")},
            customer_message=state["customer_message"],
            steps=rec.steps,
        )
        await rec.emit("orchestrator", TraceEventType.DECISION, {"final_status": result.status.value})
        return result

    async def _abort(self, rec: RunRecorder, reason: EscalationReason, detail: str) -> OnboardingResult:
        escalation = Escalation(reason=reason, detail=detail, proposed_solution="Revisión manual completa por un asesor.")
        await rec.emit("orchestrator", TraceEventType.ESCALATION, {"handoff": "asesor", **escalation.model_dump(mode="json")})
        return OnboardingResult(
            trace_id=rec.trace_id,
            status=OnboardingStatus.ESCALATED,
            escalation=escalation,
            results={},
            customer_message=fallback_message(OnboardingStatus.ESCALATED),
            steps=rec.steps,
        )
