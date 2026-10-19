from dataclasses import dataclass
from functools import lru_cache

from aio_pika import ExchangeType
from taskiq_aio_pika import AioPikaBroker, Exchange, Queue, QueueType

from app.core.config import get_config
from app.core.disposer import reg_to_dispose

EXCHANGE_NAME = "events"
EVENTS_QUEUE = "events"
TELEGRAM_QUEUE = "telegram"


def _broker(queue_name: str) -> AioPikaBroker:
    return AioPikaBroker(
        get_config().rabbitmq_url,
        exchange=Exchange(
            name=EXCHANGE_NAME,
            type=ExchangeType.DIRECT,
        ),
    ).with_queues(
        Queue(
            name=queue_name,
            routing_key=queue_name,
            type=QueueType.CLASSIC,
            durable=True,
        )
    )


@dataclass(frozen=True, slots=True)
class Brokers:
    common_broker: AioPikaBroker
    telegram_broker: AioPikaBroker


@lru_cache
def get_brokers() -> Brokers:
    brokers = Brokers(
        common_broker=_broker(EVENTS_QUEUE),
        telegram_broker=_broker(TELEGRAM_QUEUE),
    )

    async def _close() -> None:
        for broker in (brokers.common_broker, brokers.telegram_broker):
            if broker.write_conn is None:
                continue
            await broker.shutdown()

    reg_to_dispose(_close)
    return brokers
