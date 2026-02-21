"""
Configuración por entornos para ArqueoTrack 2.0
"""

import os


class BaseConfig:
    """Configuración base compartida por todos los entornos."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Archivos
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Caché
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.environ.get('LOG_FORMAT', 'console')  # console | json


class DevelopmentConfig(BaseConfig):
    """Configuración para desarrollo local."""

    DEBUG = True
    TESTING = False

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///arqueotrack.db'
    )

    # Logging detallado en desarrollo
    LOG_LEVEL = 'DEBUG'
    LOG_FORMAT = 'console'

    # Caché en memoria (simple)
    CACHE_TYPE = 'SimpleCache'


class TestingConfig(BaseConfig):
    """Configuración para tests."""

    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False

    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # Sin caché en tests
    CACHE_TYPE = 'NullCache'

    LOG_LEVEL = 'WARNING'


class ProductionConfig(BaseConfig):
    """Configuración para producción."""

    DEBUG = False
    TESTING = False

    # PostgreSQL obligatorio en producción
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL es obligatoria en producción.")

    # Pool de conexiones para PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20,
    }

    # Redis como backend de caché
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 600

    LOG_LEVEL = 'INFO'
    LOG_FORMAT = 'json'


# Mapa de entornos
_configs = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}


def get_config(env_name: str = None) -> BaseConfig:
    """
    Retorna la configuración correspondiente al entorno.

    Args:
        env_name: Nombre del entorno. Si no se especifica, lee FLASK_ENV.

    Returns:
        Clase de configuración.
    """
    env = env_name or os.environ.get('FLASK_ENV', 'development')
    config_class = _configs.get(env, DevelopmentConfig)
    return config_class()
