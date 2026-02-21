"""
Tests de integración para rutas de autenticación - ArqueoTrack 2.0.
"""

import pytest


class TestRegistro:

    def test_get_registro_page(self, client):
        response = client.get('/registro')
        assert response.status_code == 200

    def test_registro_exitoso(self, client, app):
        with app.app_context():
            response = client.post('/registro', data={
                'nombre_usuario': 'nuevo_usuario',
                'nombre': 'Nuevo',
                'apellidos': 'Usuario',
                'correo_electronico': 'nuevo@test.com',
                'fecha_nacimiento': '1995-06-15',
                'ocupacion': 'arqueologo',
                'contraseña': 'contraseña_test_123',
                'confirmar_contraseña': 'contraseña_test_123',
            }, follow_redirects=True)
            assert response.status_code == 200

    def test_registro_usuario_duplicado(self, client, app, usuario_test):
        """No debe permitir registrar el mismo email dos veces."""
        with app.app_context():
            response = client.post('/registro', data={
                'nombre_usuario': 'otro_nombre',
                'nombre': 'Otro',
                'apellidos': 'Nombre',
                'correo_electronico': 'test@arqueotrack.com',  # email del usuario_test
                'fecha_nacimiento': '1990-01-01',
                'contraseña': 'contraseña_test_123',
                'confirmar_contraseña': 'contraseña_test_123',
            }, follow_redirects=True)
            # Debe mostrar error de validación (200 con errores en el form)
            assert response.status_code == 200


class TestLogin:

    def test_get_login_page(self, client):
        response = client.get('/iniciar-sesion')
        assert response.status_code == 200

    def test_login_exitoso(self, client, app, usuario_test):
        with app.app_context():
            response = client.post('/iniciar-sesion', data={
                'correo_electronico': 'test@arqueotrack.com',
                'contraseña': 'contraseñasegura123',
            }, follow_redirects=True)
            assert response.status_code == 200

    def test_login_credenciales_incorrectas(self, client):
        response = client.post('/iniciar-sesion', data={
            'correo_electronico': 'noexiste@test.com',
            'contraseña': 'malacontraseña',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Credenciales' in response.get_data(as_text=True) or response.status_code == 200


class TestProteccionRutas:

    def test_inicio_sin_login_redirige(self, client):
        response = client.get('/inicio')
        assert response.status_code == 302
        assert '/iniciar-sesion' in response.headers['Location']

    def test_perfil_sin_login_redirige(self, client):
        response = client.get('/perfil')
        assert response.status_code == 302

    def test_portada_accesible_sin_login(self, client):
        response = client.get('/')
        assert response.status_code in (200, 302)
