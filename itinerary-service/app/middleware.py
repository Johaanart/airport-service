import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.logging_config import correlation_id_var

import logging
from fastapi import Request

logger = logging.getLogger("itinerary_service")

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        
        logger.info(f"Processing request {request.method} {request.url.path} [Correlation-ID: {correlation_id}]")
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response