"""
Utilidades de ArqueoTrack 2.0.
Importaciones centralizadas para compatibilidad.
"""

from app.utils.codes import generar_codigo_unico
from app.utils.files import allowed_file
from app.utils.time import time_ago
from app.utils.security import is_safe_url
from app.utils.constants import (
    TIPOS_HALLAZGO,
    ESTADOS_CONSERVACION,
    FASES_PREDEFINIDAS,
    TIPOS_EVENTO,
    OCUPACIONES,
    ROLES_PERMISOS,
    tiene_permiso_rol,
    # v2.0
    ROLES_INSTITUCIONALES,
    TIPOS_INSTITUCION,
    ESTADOS_CAMPANA,
    PAISES_ES,
    tiene_permiso_rol_institucional,
    # v3.0
    TIPOS_UE,
    TIPOS_RELACION_UE,
    COMPACTACIONES_UE,
    TIPOS_MUESTRA,
    TIPOS_ANALISIS,
    ESTADOS_MUESTRA,
)

__all__ = [
    'generar_codigo_unico', 'allowed_file', 'time_ago', 'is_safe_url',
    'TIPOS_HALLAZGO', 'ESTADOS_CONSERVACION', 'FASES_PREDEFINIDAS', 'TIPOS_EVENTO',
    'OCUPACIONES', 'ROLES_PERMISOS', 'tiene_permiso_rol',
    'ROLES_INSTITUCIONALES', 'TIPOS_INSTITUCION', 'ESTADOS_CAMPANA', 'PAISES_ES',
    'tiene_permiso_rol_institucional',
    'TIPOS_UE', 'TIPOS_RELACION_UE', 'COMPACTACIONES_UE',
    'TIPOS_MUESTRA', 'TIPOS_ANALISIS', 'ESTADOS_MUESTRA',
]
