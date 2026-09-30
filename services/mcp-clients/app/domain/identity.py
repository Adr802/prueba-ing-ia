from pydantic import BaseModel, Field


class IdentityVerification(BaseModel):
    verified: bool
    confidence: float = Field(ge=0.0, le=1.0)
