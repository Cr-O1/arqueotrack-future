"""
Celery Tasks - Estadísticas y Mantenimiento (v4.0)
Tareas periódicas para actualizar agregados, limpiar logs y generar resúmenes.
"""

from datetime import datetime, timedelta
import structlog

from app.tasks.celery_app import celery

log = structlog.get_logger(__name__)


@celery.task(name='tasks.actualizar_estadisticas_diarias')
def actualizar_estadisticas_diarias():
    """
    Tarea diaria (beat) que:
    - Refresca la caché de estadísticas de todos los yacimientos activos.
    - Actualiza contadores en la tabla yacimientos (denormalización).
    - Genera snapshot de actividad diaria para el dashboard.

    Programada en celery_app.py como 'actualizar-estadisticas-diario'.
    """
    from app import db
    from app.models.yacimiento import Yacimiento
    from app.models.hallazgo import Hallazgo
    from app.models.campana import Campana
    from app.models.unidad_estratigrafica import UnidadEstratigrafica
    from app.models.muestra import Muestra
    from app import cache  # Flask-Caching instance

    log.info('estadisticas.inicio')
    procesados = 0
    errores = 0

    yacimientos = Yacimiento.query.filter_by(estado='activo').all()
    for yac in yacimientos:
        try:
            stats = {
                'total_hallazgos': Hallazgo.query.filter_by(yacimiento_id=yac.id).count(),
                'total_campanas': Campana.query.filter_by(yacimiento_id=yac.id).count(),
                'total_ues': UnidadEstratigrafica.query.filter_by(yacimiento_id=yac.id).count(),
                'total_muestras': Muestra.query.filter_by(yacimiento_id=yac.id).count(),
                'actualizado_en': datetime.utcnow().isoformat(),
            }
            # Invalidar caché del yacimiento para forzar recarga fresca
            cache.delete(f'yac_stats_{yac.id}')
            cache.set(f'yac_stats_{yac.id}', stats, timeout=86400)
            procesados += 1
        except Exception as exc:
            log.error('estadisticas.yacimiento_error', yacimiento_id=yac.id, error=str(exc))
            errores += 1

    log.info('estadisticas.completado', procesados=procesados, errores=errores)
    return {'procesados': procesados, 'errores': errores, 'timestamp': datetime.utcnow().isoformat()}


@celery.task(name='tasks.limpiar_audit_logs_antiguos')
def limpiar_audit_logs_antiguos(dias_retener: int = 365):
    """
    Tarea semanal (beat) que elimina audit_logs con más de `dias_retener` días.
    Por defecto mantiene 1 año de historial completo.

    Args:
        dias_retener: Número de días de historial a conservar.
    """
    from app import db
    from app.models.audit_log import AuditLog

    umbral = datetime.utcnow() - timedelta(days=dias_retener)
    try:
        eliminados = AuditLog.query.filter(AuditLog.fecha < umbral).delete(synchronize_session=False)
        db.session.commit()
        log.info('audit_cleanup.completado', eliminados=eliminados, umbral=umbral.date().isoformat())
        return {'eliminados': eliminados, 'umbral': umbral.date().isoformat()}
    except Exception as exc:
        db.session.rollback()
        log.error('audit_cleanup.error', error=str(exc))
        raise


@celery.task(name='tasks.limpiar_invitaciones_expiradas')
def limpiar_invitaciones_expiradas():
    """
    Elimina o marca como expiradas las invitaciones pendientes
    que superaron su fecha de expiración.
    """
    from app import db
    from app.models.invitacion import Invitacion

    ahora = datetime.utcnow()
    try:
        expiradas = Invitacion.query.filter(
            Invitacion.estado == 'pendiente',
            Invitacion.fecha_expiracion < ahora,
        ).all()
        for inv in expiradas:
            inv.estado = 'expirada'
        db.session.commit()
        log.info('invitaciones_cleanup.completado', expiradas=len(expiradas))
        return {'expiradas': len(expiradas)}
    except Exception as exc:
        db.session.rollback()
        log.error('invitaciones_cleanup.error', error=str(exc))
        raise


@celery.task(name='tasks.generar_resumen_semanal')
def generar_resumen_semanal():
    """
    Genera un resumen de la actividad de la semana anterior para cada usuario:
    - Nuevos hallazgos en sus yacimientos.
    - Muestras con resultados disponibles.
    - Cambios de estado en campañas activas.

    Los datos se almacenan en caché para consumo desde el dashboard.
    """
    from app import db, cache
    from app.models.user import Usuario
    from app.models.hallazgo import Hallazgo
    from app.models.muestra import Muestra
    from app.models.yacimiento import Yacimiento

    inicio_semana = datetime.utcnow() - timedelta(days=7)
    resumenes_generados = 0

    usuarios = Usuario.query.filter_by(activo=True).all()
    for usuario in usuarios:
        try:
            # Yacimientos propios o con colaboración
            yac_ids = [y.id for y in Yacimiento.query.filter_by(propietario_id=usuario.id).all()]

            nuevos_hallazgos = Hallazgo.query.filter(
                Hallazgo.yacimiento_id.in_(yac_ids),
                Hallazgo.fecha_registro >= inicio_semana,
            ).count() if yac_ids else 0

            muestras_con_resultado = Muestra.query.filter(
                Muestra.yacimiento_id.in_(yac_ids),
                Muestra.estado == 'resultado_disponible',
                Muestra.updated_at >= inicio_semana,
            ).count() if yac_ids else 0

            resumen = {
                'nuevos_hallazgos': nuevos_hallazgos,
                'muestras_con_resultado': muestras_con_resultado,
                'periodo': f'{inicio_semana.date()} → {datetime.utcnow().date()}',
            }
            cache.set(f'resumen_semanal_{usuario.id}', resumen, timeout=7 * 86400)
            resumenes_generados += 1
        except Exception as exc:
            log.warning('resumen_semanal.usuario_error', usuario_id=usuario.id, error=str(exc))

    log.info('resumen_semanal.completado', generados=resumenes_generados)
    return {'generados': resumenes_generados}


@celery.task(name='tasks.recalcular_estadisticas_yacimiento')
def recalcular_estadisticas_yacimiento(yacimiento_id: int):
    """
    Recalcula y actualiza en caché las estadísticas de un yacimiento específico.
    Se lanza on-demand tras operaciones que modifican contadores.

    Args:
        yacimiento_id: ID del yacimiento a recalcular.
    """
    from app.models.hallazgo import Hallazgo
    from app.models.campana import Campana
    from app.models.unidad_estratigrafica import UnidadEstratigrafica
    from app.models.muestra import Muestra
    from app import cache

    stats = {
        'total_hallazgos': Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).count(),
        'total_campanas': Campana.query.filter_by(yacimiento_id=yacimiento_id).count(),
        'total_ues': UnidadEstratigrafica.query.filter_by(yacimiento_id=yacimiento_id).count(),
        'total_muestras': Muestra.query.filter_by(yacimiento_id=yacimiento_id).count(),
        'actualizado_en': datetime.utcnow().isoformat(),
    }
    cache.delete(f'yac_stats_{yacimiento_id}')
    cache.set(f'yac_stats_{yacimiento_id}', stats, timeout=3600)
    log.info('stats.recalculadas', yacimiento_id=yacimiento_id, stats=stats)
    return stats
