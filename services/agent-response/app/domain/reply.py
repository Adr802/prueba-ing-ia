from typing import Literal

from pydantic import BaseModel, Field


class ReplyRequest(BaseModel):
    prospect_name: str
    product: str
    status: Literal["approved", "escalated", "rejected", "failed"]
    documents: list[str] = Field(default_factory=list)
    escalation_reason: str | None = None


class CustomerReply(BaseModel):
    message: str = Field(min_length=1)
