# Tareas — incrementos desplegables

Cada incremento termina con `docker compose up` funcionando y una verificación concreta.

- [x] **T1. Base + Kafka**: estructura del repo, `libs/common` (evento de traza, `TracePublisher`), compose con Kafka y creación del topic.
  Verifica: el topic `onboarding.trace` existe.
- [x] **T2. MCP servers**: `mcp-clients`, `mcp-risk`, `mcp-docs` con datos mock.
  Verifica: cada tool responde según la tabla de datos mock.
- [x] **T3. Orquestador sin agentes**: endpoint, validación, grafo con nodos stub, límites de pasos y timeout, trazas a Kafka.
  Verifica: `POST` devuelve la respuesta de contrato y los eventos aparecen en Kafka.
- [ ] **T4. Agente identidad (A2A + MCP + ToolGuard)** y conexión desde el orquestador.
  Verifica: CA2, CA4, CA6.
- [ ] **T5. Agente riesgo** en paralelo con identidad.
  Verifica: CA3.
- [ ] **T6. Agente documentación (A2A + `mcp-docs`) + propuesta de solución con LLM**.
  Verifica: CA1.
- [ ] **T7. Agente respuesta al cliente (LLM)**.
  Verifica: mensaje coherente con cada estado.
- [ ] **T8. Resiliencia**: sub-agente caído y timeout.
  Verifica: CA7.
- [ ] **T9. Entregables**: diagrama de arquitectura y de secuencia, README.
