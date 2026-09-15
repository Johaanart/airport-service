from datetime import date
from typing import Optional

from app.domain.entities import Itinerary
from app.domain.ports import (
    AirportProvider,
    AirportProviderUnavailableError,
    ItineraryRepositoryPort,
)


class ItineraryService:
    def __init__(
        self,
        repository: ItineraryRepositoryPort,
        airport_provider: AirportProvider,
    ):
        self.repository = repository
        self.airport_provider = airport_provider

    async def create(
        self,
        user_name: str,
        departure_airport_id: str,
        arrival_airport_id: str,
        travel_date: date,
        duration_minutes: int,
    ) -> Itinerary:

        await self._validate_airport(departure_airport_id)
        await self._validate_airport(arrival_airport_id)

        itinerary = Itinerary(
            user_name=user_name,
            departure_airport_id=departure_airport_id,
            arrival_airport_id=arrival_airport_id,
            travel_date=travel_date,
            duration_minutes=duration_minutes,
        )

        return self.repository.save(itinerary)

    async def get(self, itinerary_id: str) -> Optional[Itinerary]:
        return self.repository.get(itinerary_id)

    async def list(self, skip: int = 0, limit: int = 50) -> list[Itinerary]:
        return self.repository.list(skip=skip, limit=limit)

    async def update(
        self,
        itinerary_id: str,
        **fields,
    ) -> Optional[Itinerary]:

        if "departure_airport_id" in fields and fields["departure_airport_id"]:
            await self._validate_airport(fields["departure_airport_id"])

        if "arrival_airport_id" in fields and fields["arrival_airport_id"]:
            await self._validate_airport(fields["arrival_airport_id"])

        return self.repository.update(
            itinerary_id,
            **fields,
        )

    async def delete(self, itinerary_id: str) -> bool:
        return self.repository.delete(itinerary_id)

    async def _validate_airport(self, airport_id: str) -> None:
        airport = await self.airport_provider.get_airport_by_id(airport_id)

        if airport is None:
            raise ValueError(
                f"El aeropuerto '{airport_id}' no existe."
            )