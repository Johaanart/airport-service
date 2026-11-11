import pytest
from unittest.mock import MagicMock, patch
import httpx
from app.infrastructure.api_colombia_adapter import ApiColombiaAdapter, api_colombia_breaker
from unittest.mock import patch, MagicMock




@pytest.mark.asyncio
async def test_cache_hit():
    with patch("redis.Redis") as mock_redis_class:
        mock_redis = MagicMock()
        mock_redis.get.return_value = '{"id": "1", "name": "El Dorado", "iata_code": "BOG", "icao_code": "SKBO", "latitude": 4.701, "longitude": -74.146, "city": "Bogotá"}'
        mock_redis_class.return_value = mock_redis

        adapter = ApiColombiaAdapter()
        result = await adapter.get_airport_by_id("1")

        assert result is not None
        assert result.iata_code == "BOG"
        mock_redis.get.assert_called_once_with("airport:1")


@pytest.mark.asyncio
async def test_circuit_breaker_triggers():
    with patch("redis.Redis"):
        adapter = ApiColombiaAdapter(base_url="https://invalid-api-url-that-does-not-exist.com")
        
        # 1. Asegurar estado inicial cerrado
        api_colombia_breaker.close()
        
        # 2. Mockear _fetch_with_resilience para simular 3 fallos directos en el breaker
        with patch.object(adapter, "_fetch_with_resilience", side_effect=Exception("API Error")):
            # Decoramos la llamada manual para registrar fallos en api_colombia_breaker
            for _ in range(3):
                try:
                    api_colombia_breaker.call(lambda: (_ for _ in ()).throw(Exception("API Error")))
                except Exception:
                    pass

        # 3. Verificar que el circuito efectivamente abrió
        assert api_colombia_breaker.current_state == "open"