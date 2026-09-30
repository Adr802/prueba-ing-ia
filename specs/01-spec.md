# Spec — Orquestador de Onboarding Digital

## Objetivo
Un agente orquestador coordina sub-agentes especializados para procesar la solicitud de onboarding de un prospecto, controla qué tools usa cada agente, mantiene el estado entre pasos, escala a un asesor humano ante incertidumbre y registra toda la traza.

## Alcance de esta versión
- Incluido: orquestador, agente de identidad, agente de riesgo, agente de respuesta al cliente, MCP por dominio, trazabilidad en Kafka.
- Incluido también: agente de documentación como servicio A2A. Toda comunicación orquestador ↔ agentes es A2A.
- Mock: datos de las tools (dentro del MCP) y embeddings. El agente de documentación no tiene flujo de razonamiento propio: invoca `prepare_documentation` y devuelve el resultado.
- Fuera de alcance: ingesta a Vector DB, Titan real, UI del asesor.

## Contrato de entrada
`POST /api/v1/onboarding/start`
```json
{"prospect_name": "Juan Perez", "document_id": "1712345678", "product": "cuenta_ahorros"}
```
Validación: los tres campos obligatorios y no vacíos; `document_id` de 10 dígitos. Si falla → `422`.

## Contrato de salida
```json
{
  "trace_id": "uuid",
  "status": "approved | escalated | rejected | failed",
  "escalation": {"reason": "...", "proposed_solution": "..."} ,
  "results": {"identity": {}, "risk": {}, "documentation": {}},
  "customer_message": "texto",
  "steps": 7
}
```
`escalation` es `null` si no hubo escalamiento.

## Tools (mock)
| Tool | Retorno | Regla |
|---|---|---|
| `verify_identity(document_id)` | `{verified, confidence}` | `confidence < 0.8` → escalar |
| `check_risk_lists(name, document_id)` | `{risk_level, matches}` | `high` → escalar |
| `prepare_documentation(product, client_data)` | `{documents: [...]}` | producto desconocido → escalar |

## Allowlist
| Agente | Tools permitidas |
|---|---|
| identidad | `verify_identity` |
| riesgo | `check_risk_lists` |
| documentación | `prepare_documentation` |
| orquestador | ninguna (solo invoca agentes vía A2A) |
| respuesta | ninguna (solo LLM) |

Una llamada a una tool fuera de la allowlist se rechaza y se registra como `tool_denied`.

## Reglas de negocio
- R1. Identidad y riesgo corren en paralelo.
- R2. Documentación corre solo si R1 terminó sin escalamiento ni rechazo.
- R3. Respuesta al cliente corre siempre al final y redacta el mensaje según el estado.
- R4. `verified=false` con `confidence >= 0.8` → `rejected` (no escala: es un no claro).
- R5. `risk_level=medium` → continúa, pero se anota en la traza.
- R6. Al escalar, el orquestador propone una solución (texto del LLM) y hace handoff al asesor.
- R7. `max_steps=10`: si se alcanza → `escalated` con razón `max_steps_exceeded`.
- R8. Timeout global 30 s: si se supera → `escalated` con razón `timeout`.
- R9. Si un sub-agente no responde o falla → `escalated` con razón `agent_error`.

## Trazabilidad
Topic `onboarding.trace`. Un evento por paso, decisión, tool call, tool denegada y escalamiento:
```json
{"trace_id": "...", "step": 3, "agent": "risk", "event": "tool_call|decision|escalation|tool_denied|error",
 "payload": {}, "timestamp": "ISO-8601"}
```

## Criterios de aceptación
- CA1. `1712345678` → identidad 0.95, riesgo low → `approved`, con documentos y mensaje.
- CA2. Documento con confianza 0.6 → `escalated`, con propuesta de solución.
- CA3. Documento en lista con riesgo high → `escalated`.
- CA4. Documento no verificado con confianza alta → `rejected`.
- CA5. Cada ejecución deja en Kafka los eventos de todos sus pasos con el mismo `trace_id`.
- CA6. Un intento de tool fuera de allowlist queda como `tool_denied` y no se ejecuta.
- CA7. Un sub-agente caído → `escalated` por `agent_error` dentro de los 30 s.
