import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.logging_config import correlation_id_var


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Toma X-Correlation-Id del request si viene (por ejemplo, propagado
    desde otro microservicio), o genera uno nuevo. Lo deja disponible
    para los logs de este request y lo devuelve en la respuesta para que
    el llamador pueda seguir la traza.
    """

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
        token = correlation_id_var.set(correlation_id)
        try:
            response = await call_next(request)
        finally:
            correlation_id_var.reset(token)
        response.headers["X-Correlation-Id"] = correlation_id
        return response
