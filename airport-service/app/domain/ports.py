"""
Puertos: contratos que el dominio espera de las implementaciones externas.
El dominio depende de estas interfaces, nunca de una implementación concreta.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models import Airport


class AirportProvider(ABC):
    @abstractmethod
    async def get_airport_by_id(self, airport_id: str) -> Optional[Airport]:
        """Devuelve un Airport del dominio, o None si no existe."""
        raise NotImplementedError


class AirportProviderUnavailableError(Exception):
    """Se lanza cuando la API externa falla, da timeout, o responde con error."""

    pass
