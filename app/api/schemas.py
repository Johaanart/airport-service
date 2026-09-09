from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class AirportResponse(BaseModel):
    id: str
    name: str
    iata_code: Optional[str] = None
    icao_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None


class PlotlyAirportPoint(BaseModel):
    """Formato reducido, listo para consumir desde Plotly JS en el frontend."""
    name: str
    lat: float
    lon: float
    label: str


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Descripción legible del error")


# =========================
# ITINERARY SCHEMAS
# =========================

class ItineraryCreate(BaseModel):
    user_name: str = Field(..., min_length=1)
    departure_airport_id: str = Field(..., min_length=1)
    arrival_airport_id: str = Field(..., min_length=1)
    travel_date: date
    duration_minutes: int = Field(..., gt=0)


class ItineraryUpdate(BaseModel):
    user_name: Optional[str] = Field(None, min_length=1)
    departure_airport_id: Optional[str] = Field(None, min_length=1)
    arrival_airport_id: Optional[str] = Field(None, min_length=1)
    travel_date: Optional[date] = None
    duration_minutes: Optional[int] = Field(None, gt=0)


class ItineraryResponse(BaseModel):
    id: str
    user_name: str
    departure_airport_id: str
    arrival_airport_id: str
    travel_date: date
    duration_minutes: int
    status: str
    created_at: datetime