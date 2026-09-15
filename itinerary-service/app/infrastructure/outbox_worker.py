import logging
import time

from app.infrastructure.database import SessionLocal
from app.infrastructure.outbox_publisher import publish_pending_events

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 5


def run() -> None:
    logger.info("Outbox worker started")

    while True:
        db = SessionLocal()

        try:
            publish_pending_events(db)
        except Exception:
            logger.exception("Unexpected error in Outbox worker")
        finally:
            db.close()

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()