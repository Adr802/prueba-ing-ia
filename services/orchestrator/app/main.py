import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from onboarding_common.domain.tool_policy import ToolPolicy
from onboarding_common.infrastructure.kafka_trace import KafkaTracePublisher
from onboarding_common.infrastructure.llm import groq_chat_model

from app.application.graph import build_graph
from app.application.start_onboarding import StartOnboarding
from app.domain.onboarding import GLOBAL_TIMEOUT_SECONDS, MAX_STEPS
from app.infrastructure.http_api import router
from app.infrastructure.http_gateway import HttpAgentGateway
from app.infrastructure.solution_advisors import LlmSolutionAdvisor, RuleBasedSolutionAdvisor

logging.basicConfig(level=logging.INFO)

AGENT_URL_ENV = {
    "identity": "AGENT_IDENTITY_URL",
    "risk": "AGENT_RISK_URL",
    "documentation": "AGENT_DOCS_URL",
    "response": "AGENT_RESPONSE_URL",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    publisher = KafkaTracePublisher(os.environ["KAFKA_BOOTSTRAP"], os.getenv("TRACE_TOPIC", "onboarding.trace"))
    await publisher.start()
    gateway = HttpAgentGateway(
        {agent: os.environ[env] for agent, env in AGENT_URL_ENV.items()},
        timeout_seconds=GLOBAL_TIMEOUT_SECONDS,
    )
    llm = groq_chat_model()
    graph = build_graph(
        llm,
        gateway,
        LlmSolutionAdvisor(llm, fallback=RuleBasedSolutionAdvisor()),
        ToolPolicy.from_file(os.getenv("ALLOWLIST_PATH", "/config/allowlist.yaml"), "orchestrator"),
    )
    app.state.start_onboarding = StartOnboarding(graph, publisher, MAX_STEPS, GLOBAL_TIMEOUT_SECONDS)
    yield
    await gateway.close()
    await publisher.stop()


app = FastAPI(title="Onboarding Orchestrator", lifespan=lifespan)
app.include_router(router)
