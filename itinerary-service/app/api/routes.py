import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.application.itinerary_service import ItineraryService
from app.domain.ports import AirportProviderUnavailableError
from app.infrastructure.database import get_db
from app.infrastructure.repository import SqlAlchemyItineraryRepository
from app.infrastructure.http_airport_adapter import HttpAirportServiceAdapter
from app.api.schemas import ItineraryCreate, ItineraryUpdate, ItineraryResponse

logger = logging.getLogger("itinerary_service")

router = APIRouter()


def get_itinerary_service(db: Session = Depends(get_db)) -> ItineraryService:
    repository = SqlAlchemyItineraryRepository(db)
    airport_provider = HttpAirportServiceAdapter()
    return ItineraryService(repository=repository, airport_provider=airport_provider)


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/itineraries", response_model=ItineraryResponse, status_code=201)
async def create_itinerary(
    data: ItineraryCreate,
    service: ItineraryService = Depends(get_itinerary_service),
):
    try:
        return await service.create(
            user_name=data.user_name,
            departure_airport_id=data.departure_airport_id,
            arrival_airport_id=data.arrival_airport_id,
            travel_date=data.travel_date,
            duration_minutes=data.duration_minutes,
        )
    except AirportProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail="El Airport Service no está disponible.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/itineraries", response_model=list[ItineraryResponse])
async def list_itineraries(
    skip: int = 0,
    limit: int = 50,
    service: ItineraryService = Depends(get_itinerary_service),
):
    return await service.list(skip=skip, limit=limit)


@router.get("/itineraries/{itinerary_id}", response_model=ItineraryResponse)
async def get_itinerary(
    itinerary_id: str, service: ItineraryService = Depends(get_itinerary_service)
):
    itinerary = await service.get(itinerary_id)
    if itinerary is None:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado.")
    return itinerary


@router.put("/itineraries/{itinerary_id}", response_model=ItineraryResponse)
async def update_itinerary(
    itinerary_id: str,
    data: ItineraryUpdate,
    service: ItineraryService = Depends(get_itinerary_service),
):
    fields = data.model_dump(exclude_unset=True)
    try:
        itinerary = await service.update(itinerary_id, **fields)
    except AirportProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail="El Airport Service no está disponible.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if itinerary is None:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado.")
    return itinerary


@router.delete("/itineraries/{itinerary_id}", status_code=204)
async def delete_itinerary(
    itinerary_id: str, service: ItineraryService = Depends(get_itinerary_service)
):
    deleted = await service.delete(itinerary_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado.")
    return None
