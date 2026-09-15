"""
Caso de uso: obtener un aeropuerto por ID.
Orquesta el dominio sin conocer detalles de infraestructura.
"""
from typing import Optional

from app.domain.models import Airport
from app.domain.ports import AirportProvider


class GetAirportById:
    def __init__(self, provider: AirportProvider):
        self._provider = provider

    async def execute(self, airport_id: str) -> Optional[Airport]:
        return await self._provider.get_airport_by_id(airport_id)
