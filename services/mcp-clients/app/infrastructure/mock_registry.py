from app.domain.identity import IdentityVerification

_CLIENTS = {
    "1712345678": IdentityVerification(verified=True, confidence=0.95),
    "1700000001": IdentityVerification(verified=True, confidence=0.60),
    "1700000002": IdentityVerification(verified=True, confidence=0.92),
    "1700000003": IdentityVerification(verified=False, confidence=0.90),
    "1700000004": IdentityVerification(verified=True, confidence=0.90),
}
_DEFAULT = IdentityVerification(verified=True, confidence=0.85)


class MockIdentityRegistry:
    def lookup(self, document_id: str) -> IdentityVerification:
        return _CLIENTS.get(document_id, _DEFAULT)
