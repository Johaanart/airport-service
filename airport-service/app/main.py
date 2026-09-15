from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.logging_config import configure_logging
from app.middleware import CorrelationIdMiddleware

configure_logging("airport-service")

app = FastAPI(
    title="Airport Service",
    description="Microservicio de aeropuertos colombianos. Implementa el patrón Adapter sobre API Colombia.",
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
