"""
Logs estructurados en JSON con correlation ID (trace_id) propagado por
request, tal como pide la rúbrica ("Logs estructurados JSON con
correlation ID en todos los servicios"). El correlation_id viaja en un
contextvar: cualquier logger.info() dentro del ciclo de vida de un
request lo incluye automáticamente, sin tener que pasarlo a mano por
cada función.
"""
import logging
import contextvars

correlation_id_var = contextvars.ContextVar("correlation_id", default="-")


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get()
        return True


def configure_logging(service_name: str) -> None:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        f'"service": "{service_name}", '
        '"correlation_id": "%(correlation_id)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
