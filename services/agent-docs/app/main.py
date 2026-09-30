from onboarding_common.infrastructure.agent_runtime import agent_service, tool_agent, trace_publisher

from app.application.prepare_documentation_task import SYSTEM_PROMPT, PrepareDocumentationTask

publisher = trace_publisher()
use_case = PrepareDocumentationTask(tool_agent("documentation", SYSTEM_PROMPT, publisher))

app = agent_service(
    name="agent-docs",
    description="Prepara documentos requeridos. Input {product, client_data} -> {product, supported, documents, analysis}.",
    handler=use_case.handle,
    publisher=publisher,
)
