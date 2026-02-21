"""
Servicio de Hallazgos.
Centraliza la lógica de negocio: creación, edición, validaciones y caché.
"""

import os
import structlog
from typing import Optional
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app import db, cache
from app.models.hallazgo import Hallazgo
from app.models.sector import Sector
from app.utils.codes import generar_codigo_unico
from app.utils.files import allowed_file

log = structlog.get_logger(__name__)


class HallazgoService:

    @staticmethod
    def crear(
        user_id: int,
        yacimiento_id: int,
        datos: dict,
        foto: Optional[FileStorage] = None,
        upload_folder: str = 'uploads',
    ) -> Hallazgo:
        """
        Crea un nuevo hallazgo con código único y gestiona la foto.

        Args:
            user_id: ID del usuario que registra el hallazgo.
            yacimiento_id: ID del yacimiento al que pertenece.
            datos: Diccionario con los campos del hallazgo.
            foto: Archivo de foto (opcional).
            upload_folder: Directorio donde guardar la foto.

        Returns:
            Hallazgo creado y persistido.

        Raises:
            ValueError: Si los datos son inválidos.
        """
        codigo = generar_codigo_unico()
        log.info("Creando hallazgo", user_id=user_id, yacimiento_id=yacimiento_id, codigo=codigo)

        hallazgo = Hallazgo(
            user_id=user_id,
            yacimiento_id=yacimiento_id,
            encontrado_por_id=user_id,
            codigo_acceso=codigo,
            **{k: v for k, v in datos.items() if v is not None},
        )

        if foto and allowed_file(foto.filename):
            filename = secure_filename(foto.filename)
            foto.save(os.path.join(upload_folder, filename))
            hallazgo.foto = filename
            log.debug("Foto guardada", filename=filename)

        db.session.add(hallazgo)
        db.session.commit()

        # Invalida caché de estadísticas del yacimiento
        cache.delete(f'stats_yacimiento_{yacimiento_id}')

        log.info("Hallazgo creado", hallazgo_id=hallazgo.id, codigo=codigo)
        return hallazgo

    @staticmethod
    def actualizar(hallazgo: Hallazgo, datos: dict) -> Hallazgo:
        """Actualiza los campos de un hallazgo existente."""
        log.info("Actualizando hallazgo", hallazgo_id=hallazgo.id)
        for campo, valor in datos.items():
            if hasattr(hallazgo, campo) and valor is not None:
                setattr(hallazgo, campo, valor)
        db.session.commit()
        cache.delete(f'stats_yacimiento_{hallazgo.yacimiento_id}')
        return hallazgo

    @staticmethod
    def eliminar(hallazgo: Hallazgo) -> None:
        """Elimina un hallazgo y limpia caché."""
        yacimiento_id = hallazgo.yacimiento_id
        log.warning("Eliminando hallazgo", hallazgo_id=hallazgo.id)
        db.session.delete(hallazgo)
        db.session.commit()
        cache.delete(f'stats_yacimiento_{yacimiento_id}')

    @staticmethod
    @cache.memoize(timeout=300)
    def buscar_por_codigo(codigo: str) -> Optional[Hallazgo]:
        """Busca un hallazgo por su código único (cacheado 5 min)."""
        return Hallazgo.query.filter_by(codigo_acceso=codigo.upper()).first()

    @staticmethod
    @cache.memoize(timeout=600)
    def estadisticas_yacimiento(yacimiento_id: int) -> dict:
        """
        Calcula estadísticas de hallazgos de un yacimiento (cacheadas 10 min).
        """
        from sqlalchemy import func
        total = Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).count()
        por_tipo = dict(
            db.session.query(Hallazgo.tipo, func.count(Hallazgo.id))
            .filter(Hallazgo.yacimiento_id == yacimiento_id)
            .group_by(Hallazgo.tipo)
            .all()
        )
        con_foto = Hallazgo.query.filter(
            Hallazgo.yacimiento_id == yacimiento_id,
            Hallazgo.foto.isnot(None),
            Hallazgo.foto != '',
        ).count()

        return {
            'total': total,
            'por_tipo': por_tipo,
            'con_foto': con_foto,
        }
