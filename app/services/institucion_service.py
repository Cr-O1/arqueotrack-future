"""
Servicio de Instituciones — ArqueoTrack 2.0 (v2.0)
Gestiona el sistema multi-tenant: creación, membresías y permisos institucionales.
"""
import structlog
from app import db, cache
from app.models.institucion import Institucion, UsuarioInstitucion
from app.utils.constants import tiene_permiso_rol_institucional

log = structlog.get_logger(__name__)


JERARQUIA_ROLES = [
    'director_general',
    'director_proyecto',
    'arqueologo_senior',
    'arqueologo_junior',
    'tecnico_campo',
    'restaurador',
    'investigador_externo',
    'estudiante',
]


class InstitucionService:

    @staticmethod
    def crear(nombre: str, tipo: str, datos: dict, fundador_id: int) -> Institucion:
        """
        Crea una nueva institución y designa al creador como director_general.
        """
        if Institucion.query.filter_by(nombre=nombre).first():
            raise ValueError(f'Ya existe una institución con el nombre "{nombre}".')

        log.info("Creando institución", nombre=nombre, tipo=tipo, fundador_id=fundador_id)
        inst = Institucion(nombre=nombre, tipo=tipo, **datos)
        db.session.add(inst)
        db.session.flush()  # obtener ID antes de crear membresía

        membresia = UsuarioInstitucion(
            usuario_id=fundador_id,
            institucion_id=inst.id,
            rol_institucional='director_general',
        )
        db.session.add(membresia)
        db.session.commit()

        log.info("Institución creada", institucion_id=inst.id)
        return inst

    @staticmethod
    def actualizar(inst: Institucion, datos: dict) -> Institucion:
        for campo, valor in datos.items():
            if hasattr(inst, campo):
                setattr(inst, campo, valor)
        db.session.commit()
        cache.delete(f'inst_{inst.id}')
        return inst

    @staticmethod
    def añadir_miembro(institucion_id: int, usuario_id: int,
                       rol: str = 'arqueologo_junior') -> UsuarioInstitucion:
        """
        Añade un usuario a una institución o actualiza su rol si ya es miembro.
        """
        from app.utils.constants import ROLES_INSTITUCIONALES
        if rol not in ROLES_INSTITUCIONALES:
            raise ValueError(f'Rol institucional inválido: {rol}')

        existente = UsuarioInstitucion.query.filter_by(
            usuario_id=usuario_id, institucion_id=institucion_id
        ).first()

        if existente:
            if not existente.activo:
                existente.activo = True
            existente.rol_institucional = rol
            db.session.commit()
            return existente

        membresia = UsuarioInstitucion(
            usuario_id=usuario_id, institucion_id=institucion_id,
            rol_institucional=rol,
        )
        db.session.add(membresia)
        db.session.commit()
        log.info("Miembro añadido", usuario_id=usuario_id, institucion_id=institucion_id, rol=rol)
        return membresia

    @staticmethod
    def eliminar_miembro(institucion_id: int, usuario_id: int) -> None:
        membresia = UsuarioInstitucion.query.filter_by(
            usuario_id=usuario_id, institucion_id=institucion_id
        ).first()
        if membresia:
            membresia.activo = False
            from datetime import datetime
            membresia.fecha_baja = datetime.utcnow()
            db.session.commit()

    @staticmethod
    def verificar(inst: Institucion) -> Institucion:
        """Verifica administrativamente una institución."""
        from datetime import datetime
        inst.verificada = True
        inst.fecha_verificacion = datetime.utcnow()
        db.session.commit()
        log.info("Institución verificada", institucion_id=inst.id)
        return inst

    @staticmethod
    @cache.memoize(timeout=300)
    def get_instituciones_usuario(user_id: int) -> list:
        """Retorna las instituciones activas del usuario (cacheado)."""
        membresias = UsuarioInstitucion.query.filter_by(
            usuario_id=user_id, activo=True
        ).all()
        return [m.institucion for m in membresias if m.institucion and m.institucion.activa]

    @staticmethod
    def puede(user_id: int, institucion_id: int, accion: str) -> bool:
        """
        Verifica si un usuario puede realizar una acción en la institución.
        Acciones: 'gestionar_miembros' | 'crear_yacimiento' | 'ver_estadisticas' | 'verificar'
        """
        membresia = UsuarioInstitucion.query.filter_by(
            usuario_id=user_id, institucion_id=institucion_id, activo=True
        ).first()
        if not membresia:
            return False
        return tiene_permiso_rol_institucional(membresia.rol_institucional, accion)
