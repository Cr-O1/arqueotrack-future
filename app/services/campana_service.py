"""
Servicio de Campañas — ArqueoTrack 2.0 (v2.0)
"""
import structlog
from app import db, cache
from app.models.campana import Campana

log = structlog.get_logger(__name__)


class CampanaService:

    @staticmethod
    def crear(yacimiento_id: int, director_id: int, datos: dict) -> Campana:
        anio = datos.get('anio')
        nombre = datos.get('nombre')
        existe = Campana.query.filter_by(
            yacimiento_id=yacimiento_id, anio=anio, nombre=nombre
        ).first()
        if existe:
            raise ValueError(f'Ya existe una campaña "{nombre}" en {anio} para este yacimiento.')

        log.info("Creando campaña", yacimiento_id=yacimiento_id, anio=anio)
        campana = Campana(yacimiento_id=yacimiento_id, director_id=director_id, **datos)
        db.session.add(campana)
        db.session.commit()
        log.info("Campaña creada", campana_id=campana.id)
        return campana

    @staticmethod
    def actualizar(campana: Campana, datos: dict) -> Campana:
        for campo, valor in datos.items():
            if hasattr(campana, campo):
                setattr(campana, campo, valor)
        db.session.commit()
        cache.delete(f'campana_{campana.id}')
        return campana

    @staticmethod
    def añadir_miembro(campana: Campana, usuario_id: int, rol: str = 'tecnico_campo'):
        from app.models.campana import campana_equipo
        existe = db.session.execute(
            campana_equipo.select().where(
                campana_equipo.c.campana_id == campana.id,
                campana_equipo.c.usuario_id == usuario_id,
            )
        ).first()
        if not existe:
            db.session.execute(
                campana_equipo.insert().values(
                    campana_id=campana.id,
                    usuario_id=usuario_id,
                    rol_en_campana=rol,
                )
            )
            db.session.commit()

    @staticmethod
    def cambiar_estado(campana: Campana, nuevo_estado: str) -> Campana:
        estados_validos = ('planificada', 'en_curso', 'finalizada', 'publicada')
        if nuevo_estado not in estados_validos:
            raise ValueError(f'Estado inválido: {nuevo_estado}')
        campana.estado = nuevo_estado
        db.session.commit()
        log.info("Estado campaña cambiado", campana_id=campana.id, estado=nuevo_estado)
        return campana

    @staticmethod
    @cache.memoize(timeout=600)
    def estadisticas(campana_id: int) -> dict:
        campana = Campana.query.get(campana_id)
        if not campana:
            return {}
        return {
            'total_hallazgos': campana.total_hallazgos,
            'total_ues': campana.total_ues,
            'duracion_dias': campana.duracion_dias,
            'total_miembros': campana.equipo.count(),
        }
