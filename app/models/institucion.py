"""
Modelo de Institución para ArqueoTrack 2.0 (v2.0).
Soporta multi-tenancy: cada institución es un tenant independiente.
"""

import uuid
from datetime import datetime
from app import db


# ── Tabla de asociación Usuario ↔ Institución ─────────────────────────────────
class UsuarioInstitucion(db.Model):
    """Membresía de un usuario en una institución con rol institucional."""

    __tablename__ = 'usuario_institucion'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id', ondelete='CASCADE'), nullable=False)

    rol_institucional = db.Column(db.String(50), nullable=False, default='arqueologo_junior')
    # Roles: director_general | director_proyecto | arqueologo_senior |
    #        arqueologo_junior | tecnico_campo | restaurador |
    #        investigador_externo | estudiante

    activo = db.Column(db.Boolean, default=True)
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_baja = db.Column(db.DateTime)
    notas = db.Column(db.Text)

    # Relaciones
    usuario = db.relationship('Usuario', back_populates='membresias')
    institucion = db.relationship('Institucion', back_populates='membresias')

    __table_args__ = (
        db.UniqueConstraint('usuario_id', 'institucion_id', name='uq_usuario_institucion'),
        db.Index('idx_ui_usuario', 'usuario_id'),
        db.Index('idx_ui_institucion', 'institucion_id'),
    )

    def __repr__(self):
        return f'<UsuarioInstitucion {self.usuario_id} → {self.institucion_id} [{self.rol_institucional}]>'


class Institucion(db.Model):
    """
    Institución arqueológica (universidad, museo, empresa, ONG).
    Actúa como tenant en el sistema multi-tenant.
    """

    __tablename__ = 'instituciones'

    # Identificación
    id = db.Column(db.Integer, primary_key=True)
    tenant_uuid = db.Column(db.String(36), unique=True, nullable=False,
                             default=lambda: str(uuid.uuid4()))

    # Información básica
    nombre = db.Column(db.String(200), unique=True, nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    # Tipos: universidad | museo | empresa | ong | gobierno | investigacion | otro

    pais = db.Column(db.String(2))          # ISO 3166-1 alpha-2 (ES, FR, IT…)
    ciudad = db.Column(db.String(100))
    direccion = db.Column(db.String(300))

    descripcion = db.Column(db.Text)
    logo_url = db.Column(db.String(500))
    sitio_web = db.Column(db.String(200))

    # Especialidades (almacenadas como JSON; array en PG se puede activar con ARRAY)
    especialidades_json = db.Column(db.Text, default='[]')
    # Ejemplo: '["romano", "medieval", "ceramica"]'

    # Verificación por administrador
    verificada = db.Column(db.Boolean, default=False)
    fecha_verificacion = db.Column(db.DateTime)

    # Metadata
    fecha_fundacion = db.Column(db.Date)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    activa = db.Column(db.Boolean, default=True)

    # Relaciones
    membresias = db.relationship('UsuarioInstitucion', back_populates='institucion',
                                  cascade='all, delete-orphan', lazy='dynamic')
    yacimientos = db.relationship('Yacimiento', back_populates='institucion', lazy='dynamic')
    campanas = db.relationship('Campana', back_populates='institucion', lazy='dynamic')

    __table_args__ = (
        db.Index('idx_instituciones_tipo', 'tipo'),
        db.Index('idx_instituciones_pais', 'pais'),
    )

    # ── Propiedades ────────────────────────────────────────────────────────────

    @property
    def total_miembros(self) -> int:
        return self.membresias.filter_by(activo=True).count()

    @property
    def total_yacimientos(self) -> int:
        return self.yacimientos.count()

    @property
    def total_campanas(self) -> int:
        return self.campanas.count()

    @property
    def especialidades(self) -> list:
        import json
        try:
            return json.loads(self.especialidades_json or '[]')
        except Exception:
            return []

    @especialidades.setter
    def especialidades(self, value: list):
        import json
        self.especialidades_json = json.dumps(value)

    # ── Métodos ────────────────────────────────────────────────────────────────

    def get_rol_usuario(self, user_id: int):
        """Retorna el rol institucional del usuario, o None si no es miembro."""
        membresia = self.membresias.filter_by(usuario_id=user_id, activo=True).first()
        return membresia.rol_institucional if membresia else None

    def es_miembro(self, user_id: int) -> bool:
        return self.membresias.filter_by(usuario_id=user_id, activo=True).count() > 0

    def to_dict(self, include_stats: bool = False) -> dict:
        data = {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'nombre': self.nombre,
            'tipo': self.tipo,
            'pais': self.pais,
            'ciudad': self.ciudad,
            'descripcion': self.descripcion,
            'logo_url': self.logo_url,
            'sitio_web': self.sitio_web,
            'verificada': self.verificada,
            'activa': self.activa,
            'especialidades': self.especialidades,
            'fecha_creacion': self.fecha_creacion.isoformat(),
        }
        if include_stats:
            data.update({
                'total_miembros': self.total_miembros,
                'total_yacimientos': self.total_yacimientos,
                'total_campanas': self.total_campanas,
            })
        return data

    def __repr__(self):
        return f'<Institucion {self.nombre}>'
