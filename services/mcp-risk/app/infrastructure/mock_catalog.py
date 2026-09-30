from app.domain.risk import RiskAssessment, RiskLevel

_LISTS = {
    "1700000002": RiskAssessment(risk_level=RiskLevel.HIGH, matches=["OFAC-SDN", "PEP-EC"]),
    "1700000004": RiskAssessment(risk_level=RiskLevel.MEDIUM, matches=["PEP-EC"]),
}


class MockRiskListCatalog:
    def screen(self, name: str, document_id: str) -> RiskAssessment:
        return _LISTS.get(document_id, RiskAssessment(risk_level=RiskLevel.LOW))
