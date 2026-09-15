from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.infrastructure.database import engine, Base
from app.infrastructure import models  # noqa: F401 registra las tablas en Base
from app.logging_config import configure_logging
from app.middleware import CorrelationIdMiddleware

configure_logging("itinerary-service")

# En desarrollo, create_all crea las tablas si no existen. El esquema real
# versionado lo controla Alembic (ver /alembic) para producción.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Itinerary Service",
    description="Microservicio de gestión de itinerarios. Valida aeropuertos contra Airport Service.",
    version="1.0.0",
)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
