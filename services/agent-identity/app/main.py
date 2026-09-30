from onboarding_common.infrastructure.agent_runtime import agent_service, tool_agent, trace_publisher

from app.application.verify_identity_task import SYSTEM_PROMPT, VerifyIdentityTask

publisher = trace_publisher()
use_case = VerifyIdentityTask(tool_agent("identity", SYSTEM_PROMPT, publisher))

app = agent_service(
    name="agent-identity",
    description="Verifica la identidad de un prospecto. Input {document_id} -> {verified, confidence, analysis}.",
    handler=use_case.handle,
    publisher=publisher,
)
