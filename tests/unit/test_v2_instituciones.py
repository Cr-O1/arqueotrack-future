"""
Tests unitarios v2.0 — Instituciones, Campañas y Auditoría.
"""

import pytest
from datetime import date, datetime
from unittest.mock import patch, MagicMock

from app.models.institucion import Institucion, UsuarioInstitucion
from app.models.campana import Campana
from app.models.audit_log import AuditLog
from app.services.institucion_service import InstitucionService
from app.services.campana_service import CampanaService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def usuario(db, app):
    """Crea un usuario de prueba."""
    from app.models.user import Usuario
    u = Usuario(
        nombre='Ana García',
        email='ana@test.com',
        ocupacion='arqueologo',
    )
    u.set_password('testpass123')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def yacimiento(db, usuario):
    """Crea un yacimiento de prueba."""
    from app.models.yacimiento import Yacimiento
    y = Yacimiento(
        nombre='Yacimiento Test',
        descripcion='Descripción de prueba',
        propietario_id=usuario.id,
        municipio='Segovia',
        pais='ES',
        latitud=40.9429,
        longitud=-4.1088,
        estado='activo',
    )
    db.session.add(y)
    db.session.commit()
    return y


@pytest.fixture
def institucion(db, usuario):
    """Crea una institución y asocia al usuario como director_general."""
    inst = InstitucionService.crear(
        nombre='Universidad Autónoma de Madrid',
        tipo='universidad',
        fundador_id=usuario.id,
        descripcion='UAM',
        pais='ES',
    )
    return inst


# ── Tests Institución ─────────────────────────────────────────────────────────

class TestInstitucionService:

    def test_crear_institucion(self, db, usuario):
        """Crear institución asigna director_general automáticamente."""
        inst = InstitucionService.crear(
            nombre='Museo Nacional',
            tipo='museo',
            fundador_id=usuario.id,
            pais='ES',
        )
        assert inst.id is not None
        assert inst.nombre == 'Museo Nacional'
        # El fundador debe ser director_general
        mem = UsuarioInstitucion.query.filter_by(
            institucion_id=inst.id,
            usuario_id=usuario.id,
        ).first()
        assert mem is not None
        assert mem.rol == 'director_general'
        assert mem.activo is True

    def test_crear_institucion_nombre_duplicado(self, db, usuario, institucion):
        """No se puede crear dos instituciones con el mismo nombre."""
        with pytest.raises(ValueError, match='nombre'):
            InstitucionService.crear(
                nombre='Universidad Autónoma de Madrid',
                tipo='universidad',
                fundador_id=usuario.id,
            )

    def test_añadir_miembro(self, db, usuario, institucion):
        """Añadir un nuevo miembro a la institución."""
        from app.models.user import Usuario
        miembro = Usuario(nombre='Luis Pérez', email='luis@test.com')
        miembro.set_password('pass')
        db.session.add(miembro)
        db.session.commit()

        mem = InstitucionService.añadir_miembro(
            institucion_id=institucion.id,
            usuario_id=miembro.id,
            rol='arqueologo_junior',
        )
        assert mem.rol == 'arqueologo_junior'
        assert mem.activo is True

    def test_añadir_miembro_rol_invalido(self, db, usuario, institucion):
        """Rol institucional inválido lanza ValueError."""
        with pytest.raises(ValueError, match='rol'):
            InstitucionService.añadir_miembro(
                institucion_id=institucion.id,
                usuario_id=usuario.id,
                rol='jefe_supremo',
            )

    def test_eliminar_miembro_soft_delete(self, db, usuario, institucion):
        """Eliminar miembro hace soft delete (fecha_baja, activo=False)."""
        from app.models.user import Usuario
        miembro = Usuario(nombre='María Torres', email='maria@test.com')
        miembro.set_password('pass')
        db.session.add(miembro)
        db.session.commit()
        InstitucionService.añadir_miembro(institucion.id, miembro.id, 'estudiante')

        InstitucionService.eliminar_miembro(institucion.id, miembro.id)
        mem = UsuarioInstitucion.query.filter_by(
            institucion_id=institucion.id, usuario_id=miembro.id
        ).first()
        assert mem.activo is False
        assert mem.fecha_baja is not None

    def test_puede_director_general_todo(self, db, usuario, institucion):
        """director_general tiene todos los permisos."""
        assert InstitucionService.puede(usuario.id, institucion.id, 'delete') is True
        assert InstitucionService.puede(usuario.id, institucion.id, 'manage') is True

    def test_puede_estudiante_solo_leer(self, db, usuario, institucion):
        """Estudiante solo puede read_limitado."""
        from app.models.user import Usuario
        est = Usuario(nombre='Estudiante', email='est@test.com')
        est.set_password('pass')
        db.session.add(est)
        db.session.commit()
        InstitucionService.añadir_miembro(institucion.id, est.id, 'estudiante')

        assert InstitucionService.puede(est.id, institucion.id, 'read') is False
        assert InstitucionService.puede(est.id, institucion.id, 'create') is False

    def test_usuario_no_miembro_no_puede(self, db, usuario, institucion):
        """Usuario no miembro no tiene ningún permiso."""
        from app.models.user import Usuario
        externo = Usuario(nombre='Externo', email='ext@test.com')
        externo.set_password('pass')
        db.session.add(externo)
        db.session.commit()

        assert InstitucionService.puede(externo.id, institucion.id, 'read') is False

    def test_verificar_institucion(self, db, usuario, institucion):
        """Verificar una institución cambia verificada a True."""
        assert institucion.verificada is False
        InstitucionService.verificar(institucion.id)
        db.session.refresh(institucion)
        assert institucion.verificada is True

    def test_get_instituciones_usuario(self, db, usuario, institucion):
        """get_instituciones_usuario devuelve lista de instituciones del usuario."""
        instituciones = InstitucionService.get_instituciones_usuario(usuario.id)
        assert len(instituciones) >= 1
        ids = [i.id for i in instituciones]
        assert institucion.id in ids


# ── Tests Campaña ─────────────────────────────────────────────────────────────

class TestCampanaService:

    def test_crear_campana(self, db, yacimiento, usuario):
        """Crear campaña con datos válidos."""
        c = CampanaService.crear(
            yacimiento_id=yacimiento.id,
            nombre='Excavación Norte',
            anio=2025,
            director_id=usuario.id,
        )
        assert c.id is not None
        assert c.nombre == 'Excavación Norte'
        assert c.anio == 2025
        assert c.estado == 'planificada'

    def test_crear_campana_duplicada(self, db, yacimiento, usuario):
        """No se puede crear dos campañas con mismo yacimiento+año+nombre."""
        CampanaService.crear(yacimiento_id=yacimiento.id, nombre='Camp A', anio=2025, director_id=usuario.id)
        with pytest.raises(ValueError, match='ya existe'):
            CampanaService.crear(yacimiento_id=yacimiento.id, nombre='Camp A', anio=2025, director_id=usuario.id)

    def test_cambiar_estado_valido(self, db, yacimiento, usuario):
        """Transición de estado válida: planificada → en_curso."""
        c = CampanaService.crear(yacimiento_id=yacimiento.id, nombre='Camp B', anio=2025, director_id=usuario.id)
        CampanaService.cambiar_estado(c.id, 'en_curso')
        db.session.refresh(c)
        assert c.estado == 'en_curso'

    def test_cambiar_estado_invalido(self, db, yacimiento, usuario):
        """Estado inválido lanza ValueError."""
        c = CampanaService.crear(yacimiento_id=yacimiento.id, nombre='Camp C', anio=2025, director_id=usuario.id)
        with pytest.raises(ValueError):
            CampanaService.cambiar_estado(c.id, 'estado_inexistente')

    def test_estadisticas_campana(self, db, yacimiento, usuario):
        """estadisticas() devuelve dict con campos esperados."""
        c = CampanaService.crear(
            yacimiento_id=yacimiento.id, nombre='Camp Stats', anio=2025,
            director_id=usuario.id,
            fecha_inicio=date(2025, 3, 1),
            fecha_fin=date(2025, 9, 30),
        )
        stats = CampanaService.estadisticas(c.id)
        assert 'total_hallazgos' in stats
        assert 'total_ues' in stats
        assert 'total_muestras' in stats
        assert 'total_miembros' in stats
        assert stats['duracion_dias'] == (date(2025, 9, 30) - date(2025, 3, 1)).days

    def test_actualizar_campana(self, db, yacimiento, usuario):
        """Actualizar campos de una campaña."""
        c = CampanaService.crear(yacimiento_id=yacimiento.id, nombre='Camp Upd', anio=2025, director_id=usuario.id)
        CampanaService.actualizar(c.id, objetivos='Nuevos objetivos', presupuesto=50000.0)
        db.session.refresh(c)
        assert c.objetivos == 'Nuevos objetivos'
        assert c.presupuesto == 50000.0


# ── Tests AuditLog ─────────────────────────────────────────────────────────────

class TestAuditLog:

    def test_registrar_crea_entrada(self, db, app, usuario, yacimiento):
        """AuditService.registrar crea una entrada en audit_logs."""
        from app.services.audit_service import AuditService
        with app.test_request_context('/'):
            from flask_login import login_user
            login_user(usuario)
            AuditService.registrar('create', 'hallazgo', 42, yacimiento_id=yacimiento.id)

        log = AuditLog.query.filter_by(
            entidad_tipo='hallazgo',
            entidad_id=42,
        ).first()
        assert log is not None
        assert log.operacion == 'create'
        assert log.exitoso is True

    def test_audit_log_campos(self, db, app, usuario, yacimiento):
        """AuditLog registra datos_antes y datos_despues."""
        from app.services.audit_service import AuditService
        with app.test_request_context('/'):
            from flask_login import login_user
            login_user(usuario)
            AuditService.registrar(
                'update', 'campana', 1,
                datos_antes={'estado': 'planificada'},
                datos_despues={'estado': 'en_curso'},
                yacimiento_id=yacimiento.id,
            )

        log = AuditLog.query.filter_by(entidad_tipo='campana').first()
        assert log is not None
        assert log.datos_antes == {'estado': 'planificada'}
        assert log.datos_despues == {'estado': 'en_curso'}
