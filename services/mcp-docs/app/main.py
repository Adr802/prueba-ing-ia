import os

from mcp.server.fastmcp import FastMCP

from app.application.prepare_documentation import PrepareDocumentation
from app.infrastructure.mock_requirements import MockProductRequirements

use_case = PrepareDocumentation(MockProductRequirements())
mcp = FastMCP("mcp-docs", host="0.0.0.0", port=int(os.getenv("PORT", "8203")))


@mcp.tool()
def prepare_documentation(product: str, client_data: dict) -> dict:
    """Retorna los documentos requeridos para el producto. supported=false si el producto no existe."""
    return use_case.execute(product, client_data).model_dump()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
