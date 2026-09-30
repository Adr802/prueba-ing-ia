import os

from mcp.server.fastmcp import FastMCP

from app.application.check_risk_lists import CheckRiskLists
from app.infrastructure.mock_catalog import MockRiskListCatalog

use_case = CheckRiskLists(MockRiskListCatalog())
mcp = FastMCP("mcp-risk", host="0.0.0.0", port=int(os.getenv("PORT", "8202")))


@mcp.tool()
def check_risk_lists(name: str, document_id: str) -> dict:
    """Consulta listas de riesgo. Retorna {risk_level: low|medium|high, matches: []}."""
    return use_case.execute(name, document_id).model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
