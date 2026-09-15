import json
import logging
import time

import pika
from sqlalchemy.orm import Session

from app.config import RABBITMQ_HOST, RABBITMQ_PORT
from app.infrastructure.models import OutboxEventModel

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "itinerary_events"
EVENT_ROUTING_KEY = "itinerary.created"


def publish_pending_events(db: Session) -> None:
    """
    Publica eventos pendientes del Transactional Outbox en RabbitMQ.

    Los eventos solo se marcan como publicados después de que
    RabbitMQ confirme la publicación.
    """

    events = (
        db.query(OutboxEventModel)
        .filter(OutboxEventModel.published.is_(False))
        .order_by(OutboxEventModel.created_at)
        .all()
    )

    if not events:
        return

    connection = None

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                heartbeat=30,
            )
        )

        channel = connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type="topic",
            durable=True,
        )

        for event in events:
            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=EVENT_ROUTING_KEY,
                body=json.dumps(
                    {
                        "id": event.id,
                        "event_type": event.event_type,
                        "payload": json.loads(event.payload),
                        "created_at": event.created_at.isoformat(),
                    }
                ),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                ),
            )

            event.published = True

        db.commit()

        logger.info(
            "Outbox events published",
            extra={
                "event_count": len(events),
                "exchange": EXCHANGE_NAME,
            },
        )

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to publish Outbox events"
        )

    finally:
        if connection and connection.is_open:
            connection.close()