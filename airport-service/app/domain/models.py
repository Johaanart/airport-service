"""
Modelo de dominio interno. No depende de infraestructura ni de la API externa.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Airport:
    id: str
    name: str
    iata_code: Optional[str]
    icao_code: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    city: Optional[str] = None
