"""
Adapter: traduce la estructura externa de API Colombia al modelo de dominio Airport.
Es la única pieza del sistema que conoce el formato de la API externa.
"""
import logging
from typing import Optional

import httpx

from app.domain.models import Airport
from app.domain.ports import AirportProvider, AirportProviderUnavailableError

logger = logging.getLogger("airport_service")

API_COLOMBIA_BASE_URL = "https://api-colombia.com/api/v1"
DEFAULT_TIMEOUT_SECONDS = 5.0


class ApiColombiaAdapter(AirportProvider):
    def __init__(self, base_url: str = API_COLOMBIA_BASE_URL, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self._base_url = base_url
        self._timeout = timeout

    async def get_airport_by_id(self, airport_id: str) -> Optional[Airport]:
        url = f"{self._base_url}/Airport/{airport_id}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
        except httpx.TimeoutException as exc:
            logger.error("Timeout consultando API Colombia (airport_id=%s): %s", airport_id, exc)
            raise AirportProviderUnavailableError("La API externa no respondió a tiempo") from exc
        except httpx.RequestError as exc:
            logger.error("Error de red consultando API Colombia (airport_id=%s): %s", airport_id, exc)
            raise AirportProviderUnavailableError("No se pudo contactar la API externa") from exc

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            logger.error(
                "API Colombia respondió %s para airport_id=%s: %s",
                response.status_code, airport_id, response.text[:200],
            )
            raise AirportProviderUnavailableError(
                f"La API externa respondió con error {response.status_code}"
            )

        data = response.json()
        return self._map_to_airport(data)

    @staticmethod
    def _map_to_airport(data: dict) -> Airport:
        """
        Traduce la respuesta cruda de API Colombia al modelo interno.
        Nota: valida los nombres exactos de los campos contra la respuesta real
        (GET https://api-colombia.com/api/v1/Airport/{id}) antes de la entrega,
        la API puede usar 'iataCode'/'icaoCode' o variantes similares.
        """
        return Airport(
            id=str(data.get("id")),
            name=data.get("name", ""),
            iata_code=data.get("iataCode") or data.get("iata_code"),
            icao_code=data.get("icaoCode") or data.get("icao_code"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            city=(data.get("city") or {}).get("name") if isinstance(data.get("city"), dict) else data.get("city"),
        )
