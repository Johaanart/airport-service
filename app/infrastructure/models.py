import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.infrastructure.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class ItineraryModel(Base):
    __tablename__ = "itineraries"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_name = Column(String, nullable=False)
    departure_airport_id = Column(String, nullable=False)
    arrival_airport_id = Column(String, nullable=False)
    travel_date = Column(Date, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="CREATED")
    created_at = Column(DateTime, default=datetime.utcnow)

    outbox_events = relationship(
        "OutboxEventModel",
        back_populates="itinerary"
    )


class OutboxEventModel(Base):
    """
    Tabla OUTBOX_EVENT.
    Implementa el patrón Transactional Outbox.
    """

    __tablename__ = "outbox_events"

    id = Column(String, primary_key=True, default=gen_uuid)
    itinerary_id = Column(
        String,
        ForeignKey("itineraries.id"),
        nullable=False
    )
    event_type = Column(
        String,
        nullable=False,
        default="ItineraryCreatedEvent"
    )
    payload = Column(String, nullable=False)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    itinerary = relationship(
        "ItineraryModel",
        back_populates="outbox_events"
    )