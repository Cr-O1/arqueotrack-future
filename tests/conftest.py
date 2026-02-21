"""
Fixtures globales de pytest para ArqueoTrack 2.0.
"""

import pytest
from app import create_app, db as _db
from app.models.user import Usuario
from app.models.yacimiento import Yacimiento
from app.models.hallazgo import Hallazgo


@pytest.fixture(scope='session')
def app():
    """Crea la aplicación Flask en modo testing."""
    application = create_app('testing')
    yield application


@pytest.fixture(scope='session')
def db(app):
    """Crea las tablas en la base de datos en memoria."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(scope='function')
def db_session(db):
    """Envuelve cada test en una transacción que se revierte al final."""
    connection = db.engine.connect()
    transaction = connection.begin()
    db.session.bind = connection
    yield db.session
    db.session.remove()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(app):
    """Cliente de prueba Flask."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Runner de comandos CLI Flask."""
    return app.test_cli_runner()


@pytest.fixture
def usuario_test(db_session, app):
    """Crea un usuario de prueba."""
    with app.app_context():
        usuario = Usuario(
            nombre_usuario='testuser',
            email='test@arqueotrack.com',
            nombre='Test',
            apellidos='Usuario',
            fecha_nacimiento='1990-01-01',
            ocupacion='arqueologo',
        )
        usuario.set_password('contraseñasegura123')
        db_session.add(usuario)
        db_session.flush()
        return usuario


@pytest.fixture
def yacimiento_test(db_session, usuario_test, app):
    """Crea un yacimiento de prueba."""
    with app.app_context():
        yacimiento = Yacimiento(
            user_id=usuario_test.id,
            nombre='Yacimiento de Prueba',
            ubicacion='España',
            descripcion='Yacimiento para tests',
            lat=40.416775,
            lng=-3.703790,
        )
        db_session.add(yacimiento)
        db_session.flush()
        return yacimiento


def login(client, email='test@arqueotrack.com', password='contraseñasegura123'):
    """Helper para autenticar en tests de integración."""
    return client.post('/iniciar-sesion', data={
        'correo_electronico': email,
        'contraseña': password,
    }, follow_redirects=True)
