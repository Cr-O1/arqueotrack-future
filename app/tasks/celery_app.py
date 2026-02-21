"""
Configuración de la aplicación Celery — ArqueoTrack 2.0 (v4.0)

Integración Flask + Celery:
- El contexto de aplicación Flask se crea para cada tarea.
- Broker: Redis (mismo que el caché, canal distinto).
- Backend: Redis (para almacenar resultados).
"""
import os
from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def create_celery(app=None) -> Celery:
    """
    Crea y configura la instancia de Celery vinculada a la app Flask.

    Uso típico en run.py o en el factory de la app:
        celery = create_celery(app)

    Uso en workers:
        # En shell:
        celery -A app.tasks.celery_app.celery worker --loglevel=info
        celery -A app.tasks.celery_app.celery beat --loglevel=info
    """
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    celery_instance = Celery(
        'arqueotrack',
        broker=redis_url,
        backend=redis_url,
        include=[
            'app.tasks.hallazgo_tasks',
            'app.tasks.informe_tasks',
            'app.tasks.estadisticas_tasks',
        ],
    )

    celery_instance.conf.update(
        # Serialización
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Europe/Madrid',
        enable_utc=True,

        # Rendimiento
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_reject_on_worker_lost=True,

        # Reintentos
        task_max_retries=3,
        task_default_retry_delay=60,  # segundos

        # Resultados
        result_expires=86400,  # 24 horas

        # Programación periódica (Celery Beat)
        beat_schedule={
            'actualizar-estadisticas-diario': {
                'task': 'app.tasks.estadisticas_tasks.actualizar_todas_estadisticas',
                'schedule': 86400,  # cada 24h
            },
            'limpiar-audit-logs-antiguos': {
                'task': 'app.tasks.estadisticas_tasks.limpiar_audit_logs',
                'schedule': 604800,  # cada 7 días
            },
        },
    )

    # Integración con contexto Flask
    if app is not None:
        class ContextTask(celery_instance.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery_instance.Task = ContextTask

    return celery_instance


# Instancia global (usada por workers)
celery = create_celery()
