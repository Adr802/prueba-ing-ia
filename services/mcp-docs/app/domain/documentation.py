from pydantic import BaseModel, Field


class DocumentationPackage(BaseModel):
    product: str
    supported: bool
    documents: list[str] = Field(default_factory=list)
