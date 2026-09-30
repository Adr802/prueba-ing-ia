from pydantic import BaseModel, Field

REQUIRED_TOOL = "verify_identity"


class IdentityCheck(BaseModel):
    verified: bool
    confidence: float = Field(ge=0.0, le=1.0)
    analysis: str = ""


class IdentityNotVerified(Exception):
    """The agent finished without obtaining an authoritative identity result."""
