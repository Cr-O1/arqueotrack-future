"""
Constantes globales y sistema de permisos por roles.
"""

# ── Tipos de hallazgo ─────────────────────────────────────────────────────────
TIPOS_HALLAZGO = [
    ('ceramica', 'Cerámica'),
    ('litico', 'Lítico'),
    ('metal', 'Metal'),
    ('oseo', 'Óseo / Fauna'),
    ('humano', 'Restos Humanos'),
    ('organico', 'Material Orgánico'),
    ('numismatica', 'Numismática'),
    ('arquitectonico', 'Elemento Arquitectónico'),
    ('lapidario', 'Lapidario'),
    ('vidrio', 'Vidrio'),
    ('joya', 'Joyería / Adorno'),
    ('herramienta', 'Herramienta'),
    ('arma', 'Arma'),
    ('inscripcion', 'Inscripción / Epigrafía'),
    ('otro', 'Otro'),
]

# ── Estados de conservación ───────────────────────────────────────────────────
ESTADOS_CONSERVACION = [
    ('excelente', 'Excelente'),
    ('bueno', 'Bueno'),
    ('regular', 'Regular'),
    ('deteriorado', 'Deteriorado'),
    ('fragmentado', 'Fragmentado'),
    ('restaurado', 'Restaurado'),
]

# ── Fases de proyecto predefinidas ────────────────────────────────────────────
FASES_PREDEFINIDAS = [
    ('valoracion', 'Valoración'),
    ('planificacion', 'Planificación'),
    ('excavacion', 'Excavación'),
    ('analisis', 'Análisis'),
    ('conservacion', 'Conservación'),
    ('documentacion', 'Documentación'),
    ('restauracion', 'Restauración'),
    ('exposicion', 'Exposición'),
    ('cierre', 'Cierre'),
]

# ── Tipos de evento ───────────────────────────────────────────────────────────
TIPOS_EVENTO = [
    ('hallazgo', 'Hallazgo'),
    ('reunion', 'Reunión'),
    ('cambio_estado', 'Cambio de Estado'),
    ('analisis', 'Análisis'),
    ('decision', 'Decisión'),
    ('visita', 'Visita'),
    ('entrega', 'Entrega'),
    ('otro', 'Otro'),
]

# ── Ocupaciones ───────────────────────────────────────────────────────────────
OCUPACIONES = [
    ('', 'Selecciona una opción'),
    ('arqueologo', 'Arqueólogo/a'),
    ('estudiante', 'Estudiante'),
    ('investigador', 'Investigador/a'),
    ('tecnico', 'Técnico/a de campo'),
    ('restaurador', 'Restaurador/a'),
    ('ciudadano', 'Ciudadano/a'),
    ('otro', 'Otro'),
]

# ── Sistema de permisos por rol ───────────────────────────────────────────────
ROLES_PERMISOS = {
    'visualizador': ['read'],
    'editor':       ['read', 'edit'],
    'colaborador':  ['read', 'edit', 'create'],
    'asistente':    ['read', 'edit', 'create', 'delete'],
    'propietario':  ['read', 'edit', 'create', 'delete', 'manage'],
}


def tiene_permiso_rol(rol: str, permiso: str) -> bool:
    """
    Verifica si un rol tiene un permiso específico.

    Args:
        rol: Nombre del rol ('visualizador', 'editor', etc.).
        permiso: Permiso a verificar ('read', 'create', 'edit', 'delete', 'manage').

    Returns:
        True si el rol tiene el permiso.
    """
    return permiso in ROLES_PERMISOS.get(rol, [])


# ─────────────────────────────────────────────────────────────────────────────
# v2.0 — Roles institucionales
# ─────────────────────────────────────────────────────────────────────────────

ROLES_INSTITUCIONALES = {
    'director_general':     ['*'],  # Todos los permisos
    'director_proyecto':    ['read', 'create', 'update', 'delete_propio', 'manage_campana'],
    'arqueologo_senior':    ['read', 'create', 'update'],
    'arqueologo_junior':    ['read', 'create'],
    'tecnico_campo':        ['read', 'create_hallazgo', 'create_ue'],
    'restaurador':          ['read', 'update_conservacion'],
    'investigador_externo': ['read'],
    'estudiante':           ['read_limitado'],
}

TIPOS_INSTITUCION = [
    ('universidad', 'Universidad'),
    ('museo', 'Museo'),
    ('empresa', 'Empresa de Arqueología'),
    ('ong', 'ONG / Fundación'),
    ('gobierno', 'Organismo Gubernamental'),
    ('investigacion', 'Centro de Investigación'),
    ('otro', 'Otro'),
]

ESTADOS_CAMPANA = [
    ('planificada', 'Planificada'),
    ('en_curso', 'En Curso'),
    ('finalizada', 'Finalizada'),
    ('publicada', 'Publicada'),
]

PAISES_ES = [
    ('ES', 'España'), ('FR', 'Francia'), ('PT', 'Portugal'), ('IT', 'Italia'),
    ('DE', 'Alemania'), ('GB', 'Reino Unido'), ('MX', 'México'), ('AR', 'Argentina'),
    ('PE', 'Perú'), ('CO', 'Colombia'), ('CL', 'Chile'), ('GR', 'Grecia'),
    ('EG', 'Egipto'), ('TR', 'Turquía'), ('JO', 'Jordania'), ('MA', 'Marruecos'),
    ('', 'Otro'),
]


def tiene_permiso_institucional(rol: str, permiso: str) -> bool:
    """
    Verifica si un rol institucional tiene un permiso.
    El director_general tiene '*' (todos).
    """
    permisos = ROLES_INSTITUCIONALES.get(rol, [])
    return '*' in permisos or permiso in permisos


# ─────────────────────────────────────────────────────────────────────────────
# v3.0 — Arqueología científica
# ─────────────────────────────────────────────────────────────────────────────

TIPOS_UE = [
    ('deposito', 'Depósito'),
    ('interfaz', 'Interfaz'),
    ('corte', 'Corte'),
    ('estructura', 'Estructura'),
    ('otro', 'Otro'),
]

TIPOS_RELACION_UE = [
    ('cubre', 'Cubre'),
    ('corta', 'Corta'),
    ('rellena', 'Rellena'),
    ('igual_a', 'Igual a'),
    ('se_apoya_en', 'Se apoya en'),
    ('interfaz_de', 'Es interfaz de'),
]

COMPACTACIONES_UE = [
    ('suelta', 'Suelta'),
    ('friable', 'Friable'),
    ('compacta', 'Compacta'),
    ('muy_compacta', 'Muy compacta'),
    ('cementada', 'Cementada'),
]

TIPOS_MUESTRA = [
    ('c14', 'Carbono-14 (C14)'),
    ('palinologia', 'Palinología'),
    ('antracologia', 'Antracología'),
    ('ceramica', 'Análisis Cerámico'),
    ('metalurgia', 'Análisis Metalúrgico'),
    ('fito', 'Fitolitos'),
    ('zoo', 'Zooarqueología'),
    ('sedimento', 'Análisis de Sedimento'),
    ('adn', 'ADN Antiguo'),
    ('isotopos', 'Isótopos Estables'),
    ('otro', 'Otro'),
]

TIPOS_ANALISIS = [
    ('c14', 'Datación C14'),
    ('polen', 'Análisis Polínico'),
    ('carbones', 'Análisis Antracológico'),
    ('ceramica', 'Análisis Cerámico'),
    ('metalurgia', 'Análisis Metalúrgico'),
    ('adn', 'Análisis de ADN'),
    ('isotopos', 'Isótopos Estables'),
    ('otro', 'Otro'),
]

ESTADOS_MUESTRA = [
    ('recogida', 'Recogida'),
    ('en_laboratorio', 'En Laboratorio'),
    ('resultado_disponible', 'Resultado Disponible'),
    ('publicada', 'Publicada'),
    ('descartada', 'Descartada'),
]
