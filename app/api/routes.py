import logging
import uuid

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.application.get_airport import GetAirportById
from app.application.itinerary_service import ItineraryService

from app.domain.ports import (
    AirportProviderUnavailableError,
)

from app.infrastructure.api_colombia_adapter import ApiColombiaAdapter
from app.infrastructure.database import get_db
from app.infrastructure.repository import SqlAlchemyItineraryRepository

from app.api.schemas import (
    AirportResponse,
    PlotlyAirportPoint,
    ItineraryCreate,
    ItineraryUpdate,
    ItineraryResponse,
)


logger = logging.getLogger("airport_service")

router = APIRouter()


# ============================================================
# AIRPORT SERVICE
# ============================================================

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
async def get_airport(
    airport_id: str,
    request: Request,
):
    correlation_id = request.headers.get(
        "X-Correlation-Id",
        str(uuid.uuid4()),
    )

    logger.info(
        '{"event": "get_airport_start", '
        '"airport_id": "%s", '
        '"correlation_id": "%s"}',
        airport_id,
        correlation_id,
    )

    try:
        airport = await _get_airport.execute(airport_id)

    except AirportProviderUnavailableError as exc:
        logger.error(
            '{"event": "get_airport_error", '
            '"correlation_id": "%s", '
            '"error": "%s"}',
            correlation_id,
            str(exc),
        )

        raise HTTPException(
            status_code=503,
            detail="El proveedor de aeropuertos no está disponible",
        ) from exc

    if airport is None:
        logger.info(
            '{"event": "get_airport_not_found", '
            '"airport_id": "%s", '
            '"correlation_id": "%s"}',
            airport_id,
            correlation_id,
        )

        raise HTTPException(
            status_code=404,
            detail=f"Aeropuerto {airport_id} no encontrado",
        )

    logger.info(
        '{"event": "get_airport_success", '
        '"airport_id": "%s", '
        '"correlation_id": "%s"}',
        airport_id,
        correlation_id,
    )

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
    responses={
        404: {"description": "Aeropuerto no encontrado"},
    },
)
async def get_airport_for_plotly(
    airport_id: str,
):
    """Formato reducido para consumir directamente desde Plotly."""

    airport = await _get_airport.execute(airport_id)

    if (
        airport is None
        or airport.latitude is None
        or airport.longitude is None
    ):
        raise HTTPException(
            status_code=404,
            detail="Aeropuerto no encontrado o sin coordenadas",
        )

    return PlotlyAirportPoint(
        name=airport.name,
        lat=airport.latitude,
        lon=airport.longitude,
        label=f"{airport.name} ({airport.iata_code or 's/c'})",
    )


@router.get("/health")
async def health():
    return {"status": "ok"}


# ============================================================
# ITINERARY SERVICE
# ============================================================

def get_itinerary_service(
    db: Session = Depends(get_db),
) -> ItineraryService:
    """
    Construye las dependencias necesarias para los casos de uso
    de itinerarios.
    """

    repository = SqlAlchemyItineraryRepository(db)
    airport_provider = ApiColombiaAdapter()

    return ItineraryService(
        repository=repository,
        airport_provider=airport_provider,
    )


# ============================================================
# CREATE ITINERARY
# ============================================================

@router.post(
    "/itineraries",
    response_model=ItineraryResponse,
    status_code=201,
)
async def create_itinerary(
    data: ItineraryCreate,
    service: ItineraryService = Depends(get_itinerary_service),
):
        try:
            itinerary = await service.create(
                user_name=data.user_name,
                departure_airport_id=data.departure_airport_id,
                arrival_airport_id=data.arrival_airport_id,
                travel_date=data.travel_date,
                duration_minutes=data.duration_minutes,
            )

            return itinerary

        except AirportProviderUnavailableError as exc:
            raise HTTPException(
                status_code=503,
                detail="El proveedor de aeropuertos no está disponible.",
            ) from exc

        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            ) from exc
# ============================================================
# LIST ITINERARIES
# ============================================================

@router.get(
    "/itineraries",
    response_model=list[ItineraryResponse],
)
async def list_itineraries(
    skip: int = 0,
    limit: int = 50,
    service: ItineraryService = Depends(get_itinerary_service),
):
    return await service.list(
        skip=skip,
        limit=limit,
    )


# ============================================================
# GET ITINERARY BY ID
# ============================================================

@router.get(
    "/itineraries/{itinerary_id}",
    response_model=ItineraryResponse,
)
async def get_itinerary(
    itinerary_id: str,
    service: ItineraryService = Depends(get_itinerary_service),
):
    itinerary = await service.get(itinerary_id)

    if itinerary is None:
        raise HTTPException(
            status_code=404,
            detail="Itinerario no encontrado.",
        )

    return itinerary


# ============================================================
# UPDATE ITINERARY
# ============================================================

@router.put(
    "/itineraries/{itinerary_id}",
    response_model=ItineraryResponse,
)
async def update_itinerary(
    itinerary_id: str,
    data: ItineraryUpdate,
    service: ItineraryService = Depends(get_itinerary_service),
):
    fields = data.model_dump(
        exclude_unset=True,
    )

    try:
        itinerary = await service.update(
            itinerary_id,
            **fields,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    if itinerary is None:
        raise HTTPException(
            status_code=404,
            detail="Itinerario no encontrado.",
        )

    return itinerary


# ============================================================
# DELETE ITINERARY
# ============================================================

@router.delete(
    "/itineraries/{itinerary_id}",
    status_code=204,
)
async def delete_itinerary(
    itinerary_id: str,
    service: ItineraryService = Depends(get_itinerary_service),
):
    deleted = await service.delete(itinerary_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Itinerario no encontrado.",
        )

    return None