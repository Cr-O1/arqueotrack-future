"""
Tests unitarios de modelos - ArqueoTrack 2.0.
"""

import pytest
from datetime import date
from app.models.user import Usuario
from app.models.yacimiento import Yacimiento
from app.models.hallazgo import Hallazgo
from app.models.invitacion import Invitacion
from app.utils.codes import generar_codigo_unico
from app.utils.constants import tiene_permiso_rol, ROLES_PERMISOS


class TestUsuario:

    def test_set_password_hashes_correctly(self, app):
        """El hash de contraseña no debe ser el texto en claro."""
        with app.app_context():
            usuario = Usuario(
                nombre_usuario='u1',
                email='u1@test.com',
                nombre='U',
                apellidos='Uno',
                fecha_nacimiento=date(1990, 1, 1),
            )
            usuario.set_password('micontraseña123')
            assert usuario.contraseña != 'micontraseña123'

    def test_check_password_valid(self, app):
        with app.app_context():
            usuario = Usuario(
                nombre_usuario='u2',
                email='u2@test.com',
                nombre='U',
                apellidos='Dos',
                fecha_nacimiento=date(1990, 1, 1),
            )
            usuario.set_password('micontraseña123')
            assert usuario.check_password('micontraseña123') is True

    def test_check_password_invalid(self, app):
        with app.app_context():
            usuario = Usuario(
                nombre_usuario='u3',
                email='u3@test.com',
                nombre='U',
                apellidos='Tres',
                fecha_nacimiento=date(1990, 1, 1),
            )
            usuario.set_password('micontraseña123')
            assert usuario.check_password('incorrecta') is False

    def test_nombre_completo(self, app):
        with app.app_context():
            usuario = Usuario(nombre='Ana', apellidos='García', nombre_usuario='x', email='x@x.com', fecha_nacimiento=date(1990, 1, 1))
            assert usuario.nombre_completo == 'Ana García'

    def test_to_dict_keys(self, app):
        with app.app_context():
            usuario = Usuario(nombre='A', apellidos='B', nombre_usuario='ab', email='ab@t.com', fecha_nacimiento=date(1990, 1, 1))
            usuario.set_password('password1234')
            d = usuario.to_dict()
            assert 'email' in d
            assert 'contraseña' not in d  # no debe exponer el hash


class TestYacimiento:

    def test_esta_activo_sin_fecha_fin(self, app):
        with app.app_context():
            y = Yacimiento(nombre='Y', user_id=1)
            assert y.esta_activo is True

    def test_esta_activo_con_fecha_fin(self, app):
        with app.app_context():
            y = Yacimiento(nombre='Y', user_id=1, fecha_fin=date(2020, 1, 1))
            assert y.esta_activo is False

    def test_to_dict_basic(self, app):
        with app.app_context():
            from datetime import datetime
            y = Yacimiento(nombre='Yac Test', user_id=1, fecha_creacion=datetime.utcnow())
            d = y.to_dict()
            assert d['nombre'] == 'Yac Test'
            assert 'esta_activo' in d


class TestGeneradorCodigo:

    def test_longitud_default(self):
        codigo = generar_codigo_unico()
        assert len(codigo) == 10

    def test_longitud_custom(self):
        codigo = generar_codigo_unico(8)
        assert len(codigo) == 8

    def test_solo_mayusculas_y_numeros(self):
        for _ in range(50):
            codigo = generar_codigo_unico()
            assert codigo.isupper() or codigo.isdigit() or all(c.isupper() or c.isdigit() for c in codigo)

    def test_codigos_distintos(self):
        codigos = {generar_codigo_unico() for _ in range(100)}
        # Con 10 chars alfanuméricos mayúsculas (36^10), la probabilidad de colisión es ínfima
        assert len(codigos) > 95


class TestPermisos:

    def test_visualizador_puede_leer(self):
        assert tiene_permiso_rol('visualizador', 'read') is True

    def test_visualizador_no_puede_crear(self):
        assert tiene_permiso_rol('visualizador', 'create') is False

    def test_colaborador_puede_crear(self):
        assert tiene_permiso_rol('colaborador', 'create') is True

    def test_colaborador_no_puede_eliminar(self):
        assert tiene_permiso_rol('colaborador', 'delete') is False

    def test_asistente_puede_eliminar(self):
        assert tiene_permiso_rol('asistente', 'delete') is True

    def test_propietario_puede_gestionar(self):
        assert tiene_permiso_rol('propietario', 'manage') is True

    def test_rol_inexistente_retorna_false(self):
        assert tiene_permiso_rol('fantasma', 'read') is False
