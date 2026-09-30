from typing import Literal

from pydantic import BaseModel, Field

REQUIRED_TOOL = "check_risk_lists"


class RiskCheck(BaseModel):
    risk_level: Literal["low", "medium", "high"]
    matches: list[str] = Field(default_factory=list)
    analysis: str = ""


class RiskNotAssessed(Exception):
    """The agent finished without obtaining an authoritative risk result."""
