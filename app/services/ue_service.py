"""
Servicio de Unidades Estratigráficas — ArqueoTrack 2.0 (v3.0)
"""
import structlog
from app import db, cache
from app.models.unidad_estratigrafica import UnidadEstratigrafica, RelacionUE

log = structlog.get_logger(__name__)


class UEService:

    @staticmethod
    def crear(yacimiento_id: int, registrado_por_id: int, datos: dict) -> UnidadEstratigrafica:
        """Crea una nueva UE con número autoasignado si no se especifica."""
        numero_ue = datos.pop('numero_ue', None)
        if numero_ue is None:
            # Autoasignar el siguiente número disponible en el yacimiento
            ultimo = (UnidadEstratigrafica.query
                      .filter_by(yacimiento_id=yacimiento_id)
                      .order_by(UnidadEstratigrafica.numero_ue.desc())
                      .first())
            numero_ue = (ultimo.numero_ue + 1) if ultimo else 1

        # Verificar que el número no esté en uso
        if UnidadEstratigrafica.query.filter_by(
            yacimiento_id=yacimiento_id, numero_ue=numero_ue
        ).first():
            raise ValueError(f'El número de UE {numero_ue} ya está en uso en este yacimiento.')

        log.info("Creando UE", yacimiento_id=yacimiento_id, numero_ue=numero_ue)
        ue = UnidadEstratigrafica(
            yacimiento_id=yacimiento_id,
            numero_ue=numero_ue,
            registrado_por_id=registrado_por_id,
            **datos,
        )
        db.session.add(ue)
        db.session.commit()
        cache.delete(f'harris_{yacimiento_id}')
        log.info("UE creada", ue_id=ue.id, numero_ue=ue.numero_ue)
        return ue

    @staticmethod
    def actualizar(ue: UnidadEstratigrafica, datos: dict) -> UnidadEstratigrafica:
        for campo, valor in datos.items():
            if hasattr(ue, campo):
                setattr(ue, campo, valor)
        db.session.commit()
        cache.delete(f'harris_{ue.yacimiento_id}')
        return ue

    @staticmethod
    def eliminar(ue: UnidadEstratigrafica) -> None:
        yacimiento_id = ue.yacimiento_id
        log.warning("Eliminando UE", ue_id=ue.id, numero_ue=ue.numero_ue)
        db.session.delete(ue)
        db.session.commit()
        cache.delete(f'harris_{yacimiento_id}')

    @staticmethod
    def marcar_excavada(ue: UnidadEstratigrafica, fecha_fin=None) -> UnidadEstratigrafica:
        from datetime import date
        ue.excavada = True
        ue.fecha_fin_excavacion = fecha_fin or date.today()
        db.session.commit()
        return ue

    @staticmethod
    def siguiente_numero(yacimiento_id: int) -> int:
        """Retorna el siguiente número disponible de UE para un yacimiento."""
        ultimo = (UnidadEstratigrafica.query
                  .filter_by(yacimiento_id=yacimiento_id)
                  .order_by(UnidadEstratigrafica.numero_ue.desc())
                  .first())
        return (ultimo.numero_ue + 1) if ultimo else 1

    @staticmethod
    @cache.memoize(timeout=120)
    def get_harris_json(yacimiento_id: int) -> dict:
        """Retorna el grafo de Harris en JSON (cacheado 2 min)."""
        from app.services.harris_service import HarrisService
        return HarrisService.exportar_json(yacimiento_id)
