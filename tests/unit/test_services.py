"""
Tests unitarios de la capa de servicios - ArqueoTrack 2.0.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from app.utils.time import time_ago
from app.utils.security import is_safe_url


class TestTimeAgo:

    def test_ninguna_fecha(self):
        assert time_ago(None) == 'desconocido'

    def test_hace_un_momento(self):
        from datetime import datetime, timedelta
        ahora = datetime.utcnow()
        assert time_ago(ahora) == 'hace un momento'

    def test_hace_minutos(self):
        from datetime import datetime, timedelta
        hace_5min = datetime.utcnow() - timedelta(minutes=5)
        resultado = time_ago(hace_5min)
        assert 'minuto' in resultado

    def test_hace_horas(self):
        from datetime import datetime, timedelta
        hace_2h = datetime.utcnow() - timedelta(hours=2)
        resultado = time_ago(hace_2h)
        assert '2 horas' in resultado

    def test_hace_dias(self):
        from datetime import datetime, timedelta
        hace_3d = datetime.utcnow() - timedelta(days=3)
        resultado = time_ago(hace_3d)
        assert '3 días' in resultado

    def test_hace_un_año(self):
        from datetime import datetime, timedelta
        hace_1año = datetime.utcnow() - timedelta(days=400)
        resultado = time_ago(hace_1año)
        assert 'año' in resultado


class TestAuthService:

    def test_registrar_usuario(self, app, db_session):
        """Debe crear un usuario en la base de datos."""
        from app.services.auth_service import AuthService
        from app.models.user import Usuario

        with app.app_context():
            usuario = AuthService.registrar({
                'nombre_usuario': 'servicio_test',
                'nombre': 'Servicio',
                'apellidos': 'Test',
                'email': 'servicio@test.com',
                'fecha_nacimiento': date(1990, 1, 1),
                'ocupacion': 'arqueologo',
                'contraseña': 'contraseña_segura_123',
            })
            assert usuario.id is not None
            assert usuario.nombre_usuario == 'servicio_test'

    def test_registrar_username_duplicado(self, app, db_session):
        """Debe lanzar ValueError si el username ya existe."""
        from app.services.auth_service import AuthService

        with app.app_context():
            datos_base = {
                'nombre_usuario': 'duplicado',
                'nombre': 'D',
                'apellidos': 'D',
                'email': 'dup1@test.com',
                'fecha_nacimiento': date(1990, 1, 1),
                'contraseña': 'contraseña_segura_123',
            }
            AuthService.registrar(datos_base)

            with pytest.raises(ValueError, match='usuario'):
                AuthService.registrar({**datos_base, 'email': 'dup2@test.com'})

    def test_autenticar_credenciales_correctas(self, app, db_session):
        """Debe retornar el usuario con credenciales válidas."""
        from app.services.auth_service import AuthService

        with app.app_context():
            AuthService.registrar({
                'nombre_usuario': 'auth_test',
                'nombre': 'Auth',
                'apellidos': 'Test',
                'email': 'auth@test.com',
                'fecha_nacimiento': date(1990, 1, 1),
                'contraseña': 'micontraseña_segura',
            })
            usuario = AuthService.autenticar('auth@test.com', 'micontraseña_segura')
            assert usuario is not None
            assert usuario.email == 'auth@test.com'

    def test_autenticar_credenciales_incorrectas(self, app, db_session):
        """Debe retornar None con contraseña incorrecta."""
        from app.services.auth_service import AuthService

        with app.app_context():
            AuthService.registrar({
                'nombre_usuario': 'auth_test2',
                'nombre': 'Auth',
                'apellidos': 'Test',
                'email': 'auth2@test.com',
                'fecha_nacimiento': date(1990, 1, 1),
                'contraseña': 'micontraseña_segura',
            })
            usuario = AuthService.autenticar('auth2@test.com', 'incorrecta')
            assert usuario is None
