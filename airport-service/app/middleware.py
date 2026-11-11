import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.logging_config import correlation_id_var

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Toma X-Correlation-Id del request si viene (por ejemplo, propagado
    desde el API Gateway o entre microservicios), o genera uno nuevo. 
    Lo deja disponible en el ContextVar para el logger y lo inyecta en la respuesta.
    """

    async def dispatch(self, request: Request, call_next):
        # 1. Capturar header (los headers en Starlette son case-insensitive)
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        token = correlation_id_var.set(correlation_id)
        
        try:
            response = await call_next(request)
            response.headers["X-Correlation-Id"] = correlation_id
            return response
        finally:
            correlation_id_var.reset(token)


