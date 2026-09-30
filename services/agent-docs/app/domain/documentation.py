from pydantic import BaseModel, Field

REQUIRED_TOOL = "prepare_documentation"


class DocumentationPackage(BaseModel):
    product: str
    supported: bool
    documents: list[str] = Field(default_factory=list)
    analysis: str = ""


class DocumentationNotPrepared(Exception):
    """The agent finished without obtaining the documentation package."""
