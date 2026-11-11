"""
Adapter: traduce la estructura externa de API Colombia al modelo de dominio Airport.
Es la única pieza del sistema que conoce el formato de la API externa.

Particularidades de API Colombia que este adapter corrige:
- El código OACI (ICAO) viene en el campo "oaciCode", no "icaoCode".
- Latitud y longitud pueden venir invertidas (ej. latitude=-75.76, longitude=4.45
  para Armenia). Se detecta con el rango geográfico de Colombia y se corrige.

Mejoras de resiliencia y performance (Nivel 2):
- Redis Cache con fallback en caso de desconexión del broker de memoria.
- Circuit Breaker con PyBreaker para evitar cascadas de fallos si la API cae.
- Exponential Backoff con Tenacity para reintentos transparentes ante fallos de red.
"""
import json
import logging
import os
from typing import Optional

import httpx
import pybreaker
import redis 
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.domain.models import Airport
from app.domain.ports import AirportProvider, AirportProviderUnavailableError

logger = logging.getLogger("airport_service")

API_COLOMBIA_BASE_URL = "https://api-colombia.com/api/v1"
DEFAULT_TIMEOUT_SECONDS = 5.0

# Rango aproximado de Colombia, incluyendo San Andrés y Leticia.
COLOMBIA_LAT_RANGE = (-5.0, 14.0)
COLOMBIA_LON_RANGE = (-83.0, -66.0)

# Configuración del Circuit Breaker: 3 fallos seguidos abren el circuito por 30s
api_colombia_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=30,
    name="APIColombiaCircuitBreaker"
)


def _in_range(value: float, bounds: tuple) -> bool:
    return bounds[0] <= value <= bounds[1]


def normalize_coordinates(latitude: Optional[float], longitude: Optional[float]):
    """Devuelve (lat, lon); si API Colombia los trae invertidos, los intercambia."""
    if latitude is None or longitude is None:
        return latitude, longitude

    as_given = _in_range(latitude, COLOMBIA_LAT_RANGE) and _in_range(longitude, COLOMBIA_LON_RANGE)
    swapped = _in_range(longitude, COLOMBIA_LAT_RANGE) and _in_range(latitude, COLOMBIA_LON_RANGE)

    if not as_given and swapped:
        return longitude, latitude
    return latitude, longitude


class ApiColombiaAdapter(AirportProvider):
    def __init__(self, base_url: str = API_COLOMBIA_BASE_URL, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self._base_url = base_url
        self._timeout = timeout
        
        # Conexión Redis con fallback robusto
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        self._cache_ttl = int(os.getenv("REDIS_TTL", 3600))
        
        try:
            self._redis = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=0, 
                decode_responses=True,
                socket_timeout=2.0
            )
        except Exception as exc:
            logger.warning("No se pudo instanciar el cliente Redis: %s", exc)
            self._redis = None

    async def get_airport_by_id(self, airport_id: str) -> Optional[Airport]:
        cache_key = f"airport:{airport_id}"

        # 1. Intento de lectura desde Redis Cache
        if self._redis:
            try:
                cached_data = self._redis.get(cache_key)
                if cached_data:
                    logger.info("[CACHE HIT] Aeropuerto id=%s devuelto desde Redis", airport_id)
                    data_dict = json.loads(cached_data)
                    return Airport(**data_dict)
            except redis.RedisError as exc:
                logger.warning("[REDIS READ ERROR] Fallback directo a API externa: %s", exc)

        logger.info("[CACHE MISS] Consultando API pública para airport_id=%s", airport_id)

        # 2. Petición protegida por Circuit Breaker y Exponential Backoff
        try:
            raw_data = await self._fetch_with_resilience(airport_id)
        except pybreaker.CircuitBreakerError as exc:
            logger.error("Circuit Breaker ABIERTO para API Colombia (airport_id=%s)", airport_id)
            raise AirportProviderUnavailableError("Servicio externo temporalmente no disponible (Circuit Breaker Abierto)") from exc
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            logger.error("Error de conexión consumiendo API Colombia tras reintentos: %s", exc)
            raise AirportProviderUnavailableError("No se pudo contactar la API externa tras varios reintentos") from exc

        if raw_data is None:
            return None

        airport = self._map_to_airport(raw_data)

        # 3. Almacenamiento en Redis Cache
# 3. Almacenamiento en Redis Cache
        if self._redis and airport:
            try:
                # Extrae los atributos de forma universal
                airport_dict = getattr(airport, "model_dump", getattr(airport, "dict", None))
                data_to_store = airport_dict() if callable(airport_dict) else airport.__dict__
                
                self._redis.setex(cache_key, self._cache_ttl, json.dumps(data_to_store))
                logger.info("[CACHE STORE] Aeropuerto id=%s guardado en Redis (%ss TTL)", airport_id, self._cache_ttl)
            except redis.RedisError as exc:
                logger.warning("[REDIS WRITE ERROR] No se pudo escribir en caché: %s", exc)
        return airport

    @api_colombia_breaker
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.RequestError)),
        reraise=True
    )
    async def _fetch_with_resilience(self, airport_id: str) -> Optional[dict]:
        """Petición HTTP asíncrona protegida con Retry y Circuit Breaker."""
        url = f"{self._base_url}/Airport/{airport_id}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url)

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

            return response.json()

    @staticmethod
    def _map_to_airport(data: dict) -> Airport:
        """Traduce la respuesta cruda de API Colombia al modelo interno."""
        latitude, longitude = normalize_coordinates(data.get("latitude"), data.get("longitude"))
        city = data.get("city")

        return Airport(
            id=str(data.get("id")),
            name=data.get("name", ""),
            iata_code=data.get("iataCode") or data.get("iata_code"),
            icao_code=data.get("oaciCode") or data.get("icaoCode") or data.get("icao_code"),
            latitude=latitude,
            longitude=longitude,
            city=city.get("name") if isinstance(city, dict) else city,
        )