import os

from mcp.server.fastmcp import FastMCP

from app.application.verify_identity import VerifyIdentity
from app.infrastructure.mock_registry import MockIdentityRegistry

use_case = VerifyIdentity(MockIdentityRegistry())
mcp = FastMCP("mcp-clients", host="0.0.0.0", port=int(os.getenv("PORT", "8201")))


@mcp.tool()
def verify_identity(document_id: str) -> dict:
    """Verifica la identidad de un documento. Retorna {verified, confidence}."""
    return use_case.execute(document_id).model_dump()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
