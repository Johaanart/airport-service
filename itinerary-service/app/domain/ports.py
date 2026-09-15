"""
Puertos: contratos que el dominio de Itinerarios espera de sus
dependencias externas. El dominio depende de estas interfaces, nunca de
una implementación concreta.

Nota de límites de contexto (DDD): este servicio NO conoce la entidad
Airport del contexto Airports (eso viviría en otro bounded context /
otro repo de código). Solo necesita saber si un aeropuerto existe, así
que el puerto expone un dict simple con lo mínimo indispensable.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities import Itinerary


class AirportProvider(ABC):
    @abstractmethod
    async def get_airport_by_id(self, airport_id: str) -> Optional[dict]:
        """Devuelve datos básicos del aeropuerto si existe, o None."""
        raise NotImplementedError


class AirportProviderUnavailableError(Exception):
    """Se lanza cuando el Airport Service falla, da timeout, o responde con error."""

    pass


class ItineraryRepositoryPort(ABC):
    @abstractmethod
    def save(self, itinerary: Itinerary) -> Itinerary:
        raise NotImplementedError

    @abstractmethod
    def get(self, itinerary_id: str) -> Optional[Itinerary]:
        raise NotImplementedError

    @abstractmethod
    def list(self, skip: int = 0, limit: int = 50) -> list[Itinerary]:
        raise NotImplementedError

    @abstractmethod
    def update(self, itinerary_id: str, **fields) -> Optional[Itinerary]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, itinerary_id: str) -> bool:
        raise NotImplementedError
