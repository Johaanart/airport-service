import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        String,
        primary_key=True,
        default=gen_uuid,
    )

    event_id = Column(
        String,
        nullable=False,
        unique=True,
    )

    itinerary_id = Column(
        String,
        nullable=False,
    )

    user_name = Column(
        String,
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )