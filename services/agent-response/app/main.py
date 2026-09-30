from onboarding_common.infrastructure.agent_runtime import agent_service, trace_publisher
from onboarding_common.infrastructure.llm import groq_chat_model

from app.application.compose_reply_task import ComposeReplyTask

publisher = trace_publisher()
use_case = ComposeReplyTask(groq_chat_model())

app = agent_service(
    name="agent-response",
    description="Redacta el mensaje final al prospecto. Input {prospect_name, product, status, documents, escalation_reason} -> {message}.",
    handler=use_case.handle,
    publisher=publisher,
)
