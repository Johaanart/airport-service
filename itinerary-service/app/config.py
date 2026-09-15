import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:////app/data/itinerary_service.db"
)

# URL del Airport Service.
# En Docker Compose se comunica mediante el nombre del servicio.
AIRPORT_SERVICE_URL = os.getenv(
    "AIRPORT_SERVICE_URL",
    "http://localhost:8001"
)

# Configuración de RabbitMQ.
RABBITMQ_HOST = os.getenv(
    "RABBITMQ_HOST",
    "localhost"
)

RABBITMQ_PORT = int(
    os.getenv(
        "RABBITMQ_PORT",
        "5672"
    )
)