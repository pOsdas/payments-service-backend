from faststream.rabbit import RabbitBroker, RabbitQueue

from app.core.config import get_settings


settings = get_settings()

broker = RabbitBroker(settings.rabbitmq_url)

PAYMENTS_NEW_QUEUE = RabbitQueue(
    name="payments.new",
    durable=True,
)

PAYMENTS_DLQ_QUEUE = RabbitQueue(
    name="payments.dlq",
    durable=True,
)