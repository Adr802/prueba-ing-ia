import httpx

from app.application.ports import AgentError


class HttpAgentGateway:
    """Invokes a sub-agent with POST {trace_id, step, input} to its /invoke endpoint."""

    def __init__(self, urls: dict[str, str], timeout_seconds: float):
        self._urls = urls
        self._http = httpx.AsyncClient(timeout=timeout_seconds)

    async def invoke(self, agent: str, payload: dict, trace_id: str, step: int) -> dict:
        url = self._urls.get(agent)
        if not url:
            raise AgentError(f"agente '{agent}' no configurado")
        try:
            response = await self._http.post(url, json={"trace_id": trace_id, "step": step, "input": payload})
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AgentError(f"'{agent}' no disponible: {type(exc).__name__}: {exc}") from exc
        if response.status_code != 200 or "error" in body:
            raise AgentError(f"'{agent}' falló: {body.get('error', f'HTTP {response.status_code}')}")
        return body["result"]

    async def close(self) -> None:
        await self._http.aclose()
