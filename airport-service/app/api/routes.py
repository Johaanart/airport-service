import logging

from fastapi import APIRouter, HTTPException

from app.application.get_airport import GetAirportById
from app.domain.ports import AirportProviderUnavailableError
from app.infrastructure.api_colombia_adapter import ApiColombiaAdapter
from app.api.schemas import AirportResponse, PlotlyAirportPoint

logger = logging.getLogger("airport_service")

router = APIRouter()

_provider = ApiColombiaAdapter()
_get_airport = GetAirportById(_provider)


@router.get(
    "/airports/{airport_id}",
    response_model=AirportResponse,
    responses={
        404: {"description": "Aeropuerto no encontrado"},
        503: {"description": "API externa no disponible"},
    },
)
async def get_airport(airport_id: str):
    logger.info("get_airport_start airport_id=%s", airport_id)

    try:
        airport = await _get_airport.execute(airport_id)
    except AirportProviderUnavailableError as exc:
        logger.error("get_airport_error airport_id=%s error=%s", airport_id, exc)
        raise HTTPException(
            status_code=503,
            detail="El proveedor de aeropuertos no está disponible",
        ) from exc

    if airport is None:
        logger.info("get_airport_not_found airport_id=%s", airport_id)
        raise HTTPException(status_code=404, detail=f"Aeropuerto {airport_id} no encontrado")

    logger.info("get_airport_success airport_id=%s", airport_id)

    return AirportResponse(
        id=airport.id,
        name=airport.name,
        iata_code=airport.iata_code,
        icao_code=airport.icao_code,
        latitude=airport.latitude,
        longitude=airport.longitude,
        city=airport.city,
    )


@router.get(
    "/airports/{airport_id}/plotly",
    response_model=PlotlyAirportPoint,
    responses={404: {"description": "Aeropuerto no encontrado"}},
)
async def get_airport_for_plotly(airport_id: str):
    """Formato reducido para consumir directamente desde Plotly."""
    airport = await _get_airport.execute(airport_id)

    if airport is None or airport.latitude is None or airport.longitude is None:
        raise HTTPException(status_code=404, detail="Aeropuerto no encontrado o sin coordenadas")

    return PlotlyAirportPoint(
        name=airport.name,
        lat=airport.latitude,
        lon=airport.longitude,
        label=f"{airport.name} ({airport.iata_code or 's/c'})",
    )


@router.get("/health")
async def health():
    return {"status": "ok"}
