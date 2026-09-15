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
