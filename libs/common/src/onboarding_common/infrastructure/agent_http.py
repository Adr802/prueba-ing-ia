import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# (input, trace_id, step) -> result
TaskHandler = Callable[[dict, str, int], Awaitable[dict]]


class InvokeRequest(BaseModel):
    trace_id: str
    step: int = 0
    input: dict = Field(default_factory=dict)


def build_agent_app(name: str, description: str, handler: TaskHandler, lifespan=None) -> FastAPI:
    """Agent endpoint. In: {trace_id, step, input}. Out: 200 {result} or 500 {error}."""
    app = FastAPI(title=name, description=description, lifespan=lifespan)

    @app.post("/invoke")
    async def invoke(body: InvokeRequest):
        try:
            return {"result": await handler(body.input, body.trace_id, body.step)}
        except Exception as exc:
            log.exception("agent task failed")
            return JSONResponse(status_code=500, content={"error": f"{type(exc).__name__}: {exc}"})

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "agent": name}

    return app
