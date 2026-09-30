from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TraceEventType(StrEnum):
    STEP = "step"
    TOOL_CALL = "tool_call"
    TOOL_DENIED = "tool_denied"
    DECISION = "decision"
    ESCALATION = "escalation"
    ERROR = "error"


class TraceEvent(BaseModel):
    trace_id: str
    step: int
    agent: str
    event: TraceEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
