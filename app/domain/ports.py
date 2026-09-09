"""
Puertos: contratos que el dominio espera de las implementaciones externas.

El dominio depende de estas interfaces, nunca de una implementación concreta.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models import Airport
from app.domain.entities import Itinerary


class AirportProvider(ABC):

    @abstractmethod
    async def get_airport_by_id(self, airport_id: str) -> Optional[Airport]:
        """Devuelve un Airport del dominio, o None si no existe."""
        raise NotImplementedError


class ItineraryRepositoryPort(ABC):

    @abstractmethod
    def save(self, itinerary: Itinerary) -> Itinerary:
        """Guarda un itinerario y devuelve la entidad persistida."""
        raise NotImplementedError

    @abstractmethod
    def get(self, itinerary_id: str) -> Optional[Itinerary]:
        """Busca un itinerario por su ID."""
        raise NotImplementedError

    @abstractmethod
    def list(self, skip: int = 0, limit: int = 50) -> list[Itinerary]:
        """Lista itinerarios."""
        raise NotImplementedError

    @abstractmethod
    def update(self, itinerary_id: str, **fields) -> Optional[Itinerary]:
        """Actualiza un itinerario."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, itinerary_id: str) -> bool:
        """Elimina un itinerario."""
        raise NotImplementedError


class AirportNotFoundError(Exception):
    """Se lanza cuando el proveedor externo no encuentra el aeropuerto."""
    pass


class AirportProviderUnavailableError(Exception):
    """Se lanza cuando la API externa falla, da timeout, o responde con error."""
    pass