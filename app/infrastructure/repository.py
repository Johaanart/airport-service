import json

from sqlalchemy.orm import Session

from app.domain.entities import Itinerary
from app.domain.ports import ItineraryRepositoryPort
from app.infrastructure.models import ItineraryModel, OutboxEventModel


def _to_entity(row: ItineraryModel) -> Itinerary:
    return Itinerary(
        id=row.id,
        user_name=row.user_name,
        departure_airport_id=row.departure_airport_id,
        arrival_airport_id=row.arrival_airport_id,
        travel_date=row.travel_date,
        duration_minutes=row.duration_minutes,
        status=row.status,
        created_at=row.created_at,
    )


class SqlAlchemyItineraryRepository(ItineraryRepositoryPort):

    def __init__(self, db: Session):
        self.db = db

    def save(self, itinerary: Itinerary) -> Itinerary:

        row = ItineraryModel(
            id=itinerary.id,
            user_name=itinerary.user_name,
            departure_airport_id=itinerary.departure_airport_id,
            arrival_airport_id=itinerary.arrival_airport_id,
            travel_date=itinerary.travel_date,
            duration_minutes=itinerary.duration_minutes,
            status=itinerary.status,
            created_at=itinerary.created_at,
        )

        self.db.add(row)
        self.db.flush()

        payload = json.dumps(
            {
                "itinerary_id": row.id,
                "user_name": row.user_name,
                "departure_airport_id": row.departure_airport_id,
                "arrival_airport_id": row.arrival_airport_id,
            }
        )

        outbox = OutboxEventModel(
            itinerary_id=row.id,
            event_type="ItineraryCreatedEvent",
            payload=payload,
            published=False,
        )

        self.db.add(outbox)

        self.db.commit()
        self.db.refresh(row)

        return _to_entity(row)

    def get(self, itinerary_id: str) -> Itinerary | None:

        row = (
            self.db.query(ItineraryModel)
            .filter(ItineraryModel.id == itinerary_id)
            .first()
        )

        return _to_entity(row) if row else None

    def list(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> list[Itinerary]:

        rows = (
            self.db.query(ItineraryModel)
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [_to_entity(row) for row in rows]

    def update(
        self,
        itinerary_id: str,
        **fields
    ) -> Itinerary | None:

        valid_columns = {
            column.name
            for column in ItineraryModel.__table__.columns
        }

        clean_fields = {
            key: value
            for key, value in fields.items()
            if value is not None and key in valid_columns
        }

        if not clean_fields:
            return self.get(itinerary_id)

        result = (
            self.db.query(ItineraryModel)
            .filter(ItineraryModel.id == itinerary_id)
            .update(
                clean_fields,
                synchronize_session=False
            )
        )

        if result == 0:
            self.db.rollback()
            return None

        self.db.commit()

        return self.get(itinerary_id)

    def delete(self, itinerary_id: str) -> bool:

        row = (
            self.db.query(ItineraryModel)
            .filter(ItineraryModel.id == itinerary_id)
            .first()
        )

        if row is None:
            return False

        self.db.delete(row)
        self.db.commit()

        return True