import json
import logging
import os
import time

import pika
from sqlalchemy.exc import IntegrityError

from app.database import Base, SessionLocal, engine
from app.models import Notification


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))

EXCHANGE_NAME = "itinerary_events"
QUEUE_NAME = "notification_queue"
ROUTING_KEY = "itinerary.created"

MAX_CONNECTION_ATTEMPTS = 10
RETRY_DELAY_SECONDS = 3


def create_database() -> None:
    Base.metadata.create_all(bind=engine)


def process_message(body: bytes) -> None:
    event = json.loads(body)

    event_id = event["id"]
    payload = event["payload"]

    itinerary_id = payload["itinerary_id"]
    user_name = payload["user_name"]

    message = (
        f"Itinerario {itinerary_id} creado "
        f"para el usuario {user_name}."
    )

    db = SessionLocal()

    try:
        notification = Notification(
            event_id=event_id,
            itinerary_id=itinerary_id,
            user_name=user_name,
            message=message,
        )

        db.add(notification)
        db.commit()

        logger.info(
            "Notification created",
            extra={
                "event_id": event_id,
                "itinerary_id": itinerary_id,
            },
        )

    except IntegrityError:
        db.rollback()

        logger.info(
            "Event already processed",
            extra={
                "event_id": event_id,
            },
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def callback(channel, method, properties, body) -> None:
    try:
        process_message(body)

        channel.basic_ack(
            delivery_tag=method.delivery_tag
        )

    except Exception:
        logger.exception("Failed to process notification event")

        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True,
        )


def connect_to_rabbitmq():
    for attempt in range(1, MAX_CONNECTION_ATTEMPTS + 1):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    heartbeat=30,
                )
            )

            logger.info(
                "Connected to RabbitMQ",
                extra={
                    "attempt": attempt,
                },
            )

            return connection

        except pika.exceptions.AMQPConnectionError:
            logger.warning(
                "RabbitMQ not ready, retrying",
                extra={
                    "attempt": attempt,
                    "max_attempts": MAX_CONNECTION_ATTEMPTS,
                },
            )

            if attempt == MAX_CONNECTION_ATTEMPTS:
                logger.exception(
                    "Could not connect to RabbitMQ"
                )
                raise

            time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError("Could not establish RabbitMQ connection")


def run() -> None:
    create_database()

    logger.info(
        "Starting Notification Function",
        extra={
            "rabbitmq_host": RABBITMQ_HOST,
            "rabbitmq_port": RABBITMQ_PORT,
        },
    )

    connection = connect_to_rabbitmq()
    channel = connection.channel()

    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="topic",
        durable=True,
    )

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
    )

    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=QUEUE_NAME,
        routing_key=ROUTING_KEY,
    )

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback,
    )

    logger.info(
        "Waiting for itinerary.created events"
    )

    try:
        channel.start_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    run()