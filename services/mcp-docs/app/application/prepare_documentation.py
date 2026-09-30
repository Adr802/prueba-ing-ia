from typing import Protocol

from app.domain.documentation import DocumentationPackage


class ProductRequirements(Protocol):
    def documents_for(self, product: str) -> list[str] | None: ...


class PrepareDocumentation:
    def __init__(self, requirements: ProductRequirements):
        self._requirements = requirements

    def execute(self, product: str, client_data: dict) -> DocumentationPackage:
        docs = self._requirements.documents_for(product)
        if docs is None:
            return DocumentationPackage(product=product, supported=False)
        return DocumentationPackage(product=product, supported=True, documents=docs)
