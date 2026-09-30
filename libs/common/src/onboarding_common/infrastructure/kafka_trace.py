import logging

from aiokafka import AIOKafkaProducer

from onboarding_common.domain.trace import TraceEvent

log = logging.getLogger(__name__)


class KafkaTracePublisher:
    def __init__(self, bootstrap_servers: str, topic: str = "onboarding.trace"):
        self._topic = topic
        self._bootstrap = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        # aiokafka binds to the running loop, so the producer can't be built at import time.
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap)
        await self._producer.start()

    async def publish(self, event: TraceEvent) -> None:
        # Tracing must never break the onboarding flow; failures are logged, not raised.
        try:
            await self._producer.send_and_wait(
                self._topic, event.model_dump_json().encode(), key=event.trace_id.encode()
            )
        except Exception:
            log.exception("trace publish failed for %s", event.trace_id)

    async def stop(self) -> None:
        await self._producer.stop()


class LoggingTracePublisher:
    async def start(self) -> None: ...

    async def publish(self, event: TraceEvent) -> None:
        log.info("TRACE %s", event.model_dump_json())

    async def stop(self) -> None: ...
