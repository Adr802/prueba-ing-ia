"""Smoke test: calls every MCP tool with the mock scenarios and prints the result."""
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

CASES = [
    ("http://mcp-clients:8201/mcp", "verify_identity", {"document_id": "1712345678"}),
    ("http://mcp-clients:8201/mcp", "verify_identity", {"document_id": "1700000001"}),
    ("http://mcp-risk:8202/mcp", "check_risk_lists", {"name": "Juan Perez", "document_id": "1700000002"}),
    ("http://mcp-risk:8202/mcp", "check_risk_lists", {"name": "Juan Perez", "document_id": "1712345678"}),
    ("http://mcp-docs:8203/mcp", "prepare_documentation", {"product": "cuenta_ahorros", "client_data": {}}),
    ("http://mcp-docs:8203/mcp", "prepare_documentation", {"product": "hipoteca", "client_data": {}}),
]


async def call(url: str, tool: str, args: dict) -> dict:
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, args)
            return json.loads(result.content[0].text)


async def main() -> None:
    for url, tool, args in CASES:
        print(f"{tool}({args}) -> {await call(url, tool, args)}")


asyncio.run(main())
