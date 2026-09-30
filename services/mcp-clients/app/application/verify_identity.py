from typing import Protocol

from app.domain.identity import IdentityVerification


class IdentityRegistry(Protocol):
    def lookup(self, document_id: str) -> IdentityVerification: ...


class VerifyIdentity:
    def __init__(self, registry: IdentityRegistry):
        self._registry = registry

    def execute(self, document_id: str) -> IdentityVerification:
        return self._registry.lookup(document_id)
