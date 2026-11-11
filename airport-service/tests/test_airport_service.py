from unittest.mock import patch
import pytest
import respx
from httpx import Response

from app.infrastructure.api_colombia_adapter import ApiColombiaAdapter, API_COLOMBIA_BASE_URL
from app.domain.ports import AirportProviderUnavailableError


@pytest.mark.asyncio
@respx.mock
@patch("app.infrastructure.api_colombia_adapter.redis.Redis")
async def test_get_airport_by_id_maps_response_to_domain_model(mock_redis):
    # Simular que Redis no tiene la llave en caché (Cache Miss)
    mock_redis.return_value.get.return_value = None

    respx.get(f"{API_COLOMBIA_BASE_URL}/Airport/1").mock(
        return_value=Response(
            200,
            json={
                "id": 1,
                "name": "El Dorado International Airport",
                "iataCode": "BOG",
                "oaciCode": "SKBO",
                "latitude": 4.70159,
                "longitude": -74.1469,
            },
        )
    )
    adapter = ApiColombiaAdapter()

    airport = await adapter.get_airport_by_id("1")

    assert airport is not None
    assert airport.name == "El Dorado International Airport"
    assert airport.iata_code == "BOG"
    assert airport.latitude == pytest.approx(4.70159)


@pytest.mark.asyncio
@respx.mock
@patch("app.infrastructure.api_colombia_adapter.redis.Redis")
async def test_get_airport_by_id_returns_none_when_not_found(mock_redis):
    mock_redis.return_value.get.return_value = None

    respx.get(f"{API_COLOMBIA_BASE_URL}/Airport/999").mock(return_value=Response(404))
    adapter = ApiColombiaAdapter()

    airport = await adapter.get_airport_by_id("999")

    assert airport is None


@pytest.mark.asyncio
@respx.mock
@patch("app.infrastructure.api_colombia_adapter.redis.Redis")
async def test_get_airport_by_id_raises_when_external_api_fails(mock_redis):
    mock_redis.return_value.get.return_value = None

    respx.get(f"{API_COLOMBIA_BASE_URL}/Airport/1").mock(return_value=Response(500))
    adapter = ApiColombiaAdapter()

    with pytest.raises(AirportProviderUnavailableError):
        await adapter.get_airport_by_id("1")