import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class McpToolProvider:
    def __init__(self, url: str):
        self._url = url

    async def list_tools(self) -> list[dict]:
        async with streamablehttp_client(self._url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
        return [
            {"type": "function", "function": {"name": t.name, "description": t.description or "", "parameters": t.inputSchema}}
            for t in listed.tools
        ]

    async def call(self, name: str, args: dict) -> dict:
        async with streamablehttp_client(self._url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, args)
        if result.isError:
            raise RuntimeError(f"MCP tool '{name}' falló: {result.content[0].text}")
        return json.loads(result.content[0].text)
