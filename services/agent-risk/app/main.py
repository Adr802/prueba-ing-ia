from onboarding_common.infrastructure.agent_runtime import agent_service, tool_agent, trace_publisher

from app.application.check_risk_task import SYSTEM_PROMPT, CheckRiskTask

publisher = trace_publisher()
use_case = CheckRiskTask(tool_agent("risk", SYSTEM_PROMPT, publisher))

app = agent_service(
    name="agent-risk",
    description="Consulta listas de riesgo. Input {name, document_id} -> {risk_level, matches, analysis}.",
    handler=use_case.handle,
    publisher=publisher,
)
