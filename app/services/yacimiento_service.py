"""
Servicio de Yacimientos.
"""

import structlog
from app import db, cache
from app.models.yacimiento import Yacimiento
from app.models.invitacion import Invitacion

log = structlog.get_logger(__name__)


class YacimientoService:

    @staticmethod
    def crear(user_id: int, datos: dict) -> Yacimiento:
        """Crea un nuevo yacimiento."""
        log.info("Creando yacimiento", user_id=user_id, nombre=datos.get('nombre'))
        yacimiento = Yacimiento(user_id=user_id, **datos)
        db.session.add(yacimiento)
        db.session.commit()
        log.info("Yacimiento creado", yacimiento_id=yacimiento.id)
        return yacimiento

    @staticmethod
    def actualizar(yacimiento: Yacimiento, datos: dict) -> Yacimiento:
        """Actualiza un yacimiento."""
        for campo, valor in datos.items():
            if hasattr(yacimiento, campo):
                setattr(yacimiento, campo, valor)
        db.session.commit()
        cache.delete(f'stats_yacimiento_{yacimiento.id}')
        return yacimiento

    @staticmethod
    def eliminar(yacimiento: Yacimiento) -> None:
        """Elimina un yacimiento (cascade elimina hallazgos, sectores, etc.)."""
        log.warning("Eliminando yacimiento", yacimiento_id=yacimiento.id)
        db.session.delete(yacimiento)
        db.session.commit()

    @staticmethod
    def get_accesibles(user_id: int) -> list:
        """
        Retorna todos los yacimientos accesibles por el usuario:
        propios + colaboraciones aceptadas.
        """
        propios = Yacimiento.query.filter_by(user_id=user_id).all()
        invitaciones = Invitacion.query.filter_by(
            invitado_id=user_id, estado='aceptada'
        ).all()
        colaboracion = [inv.yacimiento for inv in invitaciones]
        return propios, colaboracion

    @staticmethod
    @cache.memoize(timeout=600)
    def estadisticas_globales(user_id: int) -> dict:
        """Estadísticas globales del usuario (cacheadas)."""
        propios, colaboracion = YacimientoService.get_accesibles(user_id)
        todos = propios + colaboracion
        total_hallazgos = sum(y.total_hallazgos for y in todos)
        activos = sum(1 for y in todos if y.esta_activo)
        finalizados = sum(1 for y in todos if not y.esta_activo)
        return {
            'total_yacimientos': len(todos),
            'total_hallazgos': total_hallazgos,
            'yacimientos_activos': activos,
            'yacimientos_finalizados': finalizados,
        }
