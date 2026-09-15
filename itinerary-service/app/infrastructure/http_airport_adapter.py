"""
Adapter concreto del puerto AirportProvider para el contexto Itineraries.

IMPORTANTE: este adapter llama al AIRPORT SERVICE por HTTP (su propio
endpoint interno GET /airports/{id}), NO a la API externa API Colombia
directamente. Esa llamada directa a API Colombia es responsabilidad
exclusiva del Airport Service (él sí implementa el patrón Adapter sobre
la API externa). Aquí, Itinerary Service solo consume a su compañero de
microservicios vía HTTP, tal como exige la arquitectura de microservicios
y el diagrama de secuencia del documento.
"""

import logging
from typing import Optional

import httpx

from app.config import AIRPORT_SERVICE_URL
from app.domain.ports import AirportProvider, AirportProviderUnavailableError
from app.logging_config import correlation_id_var

logger = logging.getLogger("itinerary_service")

DEFAULT_TIMEOUT_SECONDS = 5.0


class HttpAirportServiceAdapter(AirportProvider):
    def __init__(self, base_url: str = AIRPORT_SERVICE_URL, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self._base_url = base_url
        self._timeout = timeout

    async def get_airport_by_id(self, airport_id: str) -> Optional[dict]:
        url = f"{self._base_url}/airports/{airport_id}"
        # Propaga el correlation_id de este request hacia el Airport Service,
        # para poder seguir una traza completa a través de los dos servicios.
        headers = {"X-Correlation-Id": correlation_id_var.get()}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers=headers)
        except httpx.TimeoutException as exc:
            logger.error("Timeout consultando airport-service (airport_id=%s): %s", airport_id, exc)
            raise AirportProviderUnavailableError("El Airport Service no respondió a tiempo") from exc
        except httpx.RequestError as exc:
            logger.error("Error de red consultando airport-service (airport_id=%s): %s", airport_id, exc)
            raise AirportProviderUnavailableError("No se pudo contactar el Airport Service") from exc

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            logger.error(
                "airport-service respondió %s para airport_id=%s: %s",
                response.status_code, airport_id, response.text[:200],
            )
            raise AirportProviderUnavailableError(
                f"El Airport Service respondió con error {response.status_code}"
            )

        return response.json()
