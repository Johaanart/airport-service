from dataclasses import dataclass, field
from datetime import date, datetime
import uuid


@dataclass
class Itinerary:
    """
    Entidad de dominio. Deliberadamente NO depende de SQLAlchemy ni de
    Pydantic: representa el concepto de negocio "Itinerario" tal cual lo
    define el lenguaje ubicuo del contexto Itineraries, sin importar cómo
    se persiste o cómo se expone por HTTP.
    """

    user_name: str
    departure_airport_id: str
    arrival_airport_id: str
    travel_date: date
    duration_minutes: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "CREATED"
    created_at: datetime = field(default_factory=datetime.utcnow)