from typing import Protocol

from app.domain.risk import RiskAssessment


class RiskListCatalog(Protocol):
    def screen(self, name: str, document_id: str) -> RiskAssessment: ...


class CheckRiskLists:
    def __init__(self, catalog: RiskListCatalog):
        self._catalog = catalog

    def execute(self, name: str, document_id: str) -> RiskAssessment:
        return self._catalog.screen(name, document_id)
