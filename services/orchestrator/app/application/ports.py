from typing import Protocol

from app.domain.onboarding import Escalation, OnboardingRequest


class AgentError(Exception):
    pass


class AgentGateway(Protocol):
    """Sends a task to a remote sub-agent and returns its structured result. Raises AgentError."""

    async def invoke(self, agent: str, payload: dict, trace_id: str, step: int) -> dict: ...


class SolutionAdvisor(Protocol):
    async def propose(self, request: OnboardingRequest, escalation: Escalation, results: dict) -> str: ...
