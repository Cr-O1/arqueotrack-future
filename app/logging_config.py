"""
Configuración de logging estructurado para ArqueoTrack 2.0.
Usa structlog para logs legibles en desarrollo y JSON en producción.
"""

import logging
import sys
import structlog
from flask import Flask, request, has_request_context, g
from flask_login import current_user


def add_request_context(logger, method, event_dict):
    """Añade contexto de la request HTTP al log si existe."""
    if has_request_context():
        event_dict['method'] = request.method
        event_dict['path'] = request.path
        event_dict['ip'] = request.remote_addr
        try:
            if current_user and current_user.is_authenticated:
                event_dict['user_id'] = current_user.id
        except Exception:
            pass
    return event_dict


def setup_logging(app: Flask) -> None:
    """
    Configura logging estructurado según el entorno.

    - development: logs coloridos y legibles en consola.
    - production: logs JSON para ingesta en ELK / CloudWatch.
    """
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    log_format = app.config.get('LOG_FORMAT', 'console')

    # ── Procesadores compartidos ──────────────────────────────────────────────
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_request_context,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.StackInfoRenderer(),
    ]

    if log_format == 'json':
        # ── Producción: JSON ──────────────────────────────────────────────────
        renderer = structlog.processors.JSONRenderer()
    else:
        # ── Desarrollo: consola coloreada ─────────────────────────────────────
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Silenciar librerías ruidosas
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(
        logging.INFO if app.config.get('SQLALCHEMY_ECHO') else logging.WARNING
    )

    app.logger.info(
        "Logging configurado",
        format=log_format,
        level=app.config.get('LOG_LEVEL', 'INFO'),
    )
