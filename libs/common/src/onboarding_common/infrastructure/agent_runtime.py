import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from onboarding_common.application.tool_agent import ToolAgent
from onboarding_common.application.tool_guard import ToolGuard
from onboarding_common.domain.tool_policy import ToolPolicy
from onboarding_common.infrastructure.agent_http import TaskHandler, build_agent_app
from onboarding_common.infrastructure.kafka_trace import KafkaTracePublisher
from onboarding_common.infrastructure.llm import groq_chat_model
from onboarding_common.infrastructure.mcp_tools import McpToolProvider

logging.basicConfig(level=logging.INFO)


def trace_publisher() -> KafkaTracePublisher:
    return KafkaTracePublisher(os.environ["KAFKA_BOOTSTRAP"], os.getenv("TRACE_TOPIC", "onboarding.trace"))


def tool_agent(agent: str, system_prompt: str, publisher: KafkaTracePublisher) -> ToolAgent:
    guard = ToolGuard(
        ToolPolicy.from_file(os.getenv("ALLOWLIST_PATH", "/config/allowlist.yaml"), agent),
        McpToolProvider(os.environ["MCP_URL"]),
        publisher,
    )
    return ToolAgent(groq_chat_model(), guard, system_prompt)


def agent_service(name: str, description: str, handler: TaskHandler, publisher) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app):
        await publisher.start()
        yield
        await publisher.stop()

    return build_agent_app(name, description, handler, lifespan=lifespan)
