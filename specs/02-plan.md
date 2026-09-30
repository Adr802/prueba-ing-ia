# Plan técnico

## Stack
- Python 3.12, FastAPI, LangGraph, SDK `a2a-sdk` (protocolo A2A), SDK `mcp` (transporte streamable HTTP).
- LLM: Groq `openai/gpt-oss-20b` (configurable con `GROQ_MODEL`) vía `langchain-groq` (`GROQ_API_KEY` en `.env`).
- Embeddings: puerto `EmbeddingProvider` con adapter `FakeEmbedding` (Titan v2 queda como adapter futuro).
- Kafka en modo KRaft (sin zookeeper), cliente `aiokafka`.
- Docker Compose, un contenedor por servicio.

## Servicios
| Servicio | Puerto | Rol |
|---|---|---|
| `orchestrator` | 8000 | API REST + grafo LangGraph + cliente A2A |
| `agent-identity` | 8101 | Servidor A2A, usa `mcp-clients` |
| `agent-risk` | 8102 | Servidor A2A, usa `mcp-risk` |
| `agent-response` | 8103 | Servidor A2A, solo LLM |
| `agent-docs` | 8104 | Servidor A2A, usa `mcp-docs` |
| `mcp-clients` | 8201 | Tool `verify_identity` (mock) |
| `mcp-risk` | 8202 | Tool `check_risk_lists` (mock) |
| `mcp-docs` | 8203 | Tool `prepare_documentation` (mock) |
| `kafka` | 9092 | Topic `onboarding.trace` |

## Estructura hexagonal (por servicio)
```
services/<svc>/app/
  domain/          # entidades, reglas (umbrales), sin dependencias externas
  application/     # casos de uso, puertos (interfaces), grafo LangGraph
  infrastructure/  # adapters: http/a2a entrante, mcp cliente, kafka, llm
  main.py          # composición (inyecta adapters en puertos)
```
Código común (evento de traza, puerto `TracePublisher`, adapter Kafka) en `libs/common`.

## Grafo del orquestador
`validate → [identity ‖ risk] → evaluate → documentation → response → END`
Si `evaluate` detecta escalamiento/rechazo, salta a `propose_solution → response`.
Contador de pasos en el estado; `asyncio.wait_for(..., 30)` envuelve la ejecución.

## Allowlist
`config/allowlist.yaml` cargado por cada servicio. Un `ToolGuard` envuelve el cliente MCP: valida y publica `tool_denied` antes de llamar.

## Datos mock (dentro de cada tool)
| document_id | identidad | riesgo |
|---|---|---|
| 1712345678 | verified, 0.95 | low |
| 1700000001 | verified, 0.60 | low |
| 1700000002 | verified, 0.92 | high |
| 1700000003 | not verified, 0.90 | low |
| 1700000004 | verified, 0.90 | medium |
| otro | verified, 0.85 | low |
