"""
Modelo de Usuario — ArqueoTrack 2.0 (actualizado para v2.0 + v3.0)
"""
from datetime import datetime
from flask_login import UserMixin
from app import bcrypt, db
from app.utils.constants import tiene_permiso_rol


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    contraseña = db.Column('password_hash', db.String(200), nullable=False)

    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    ocupacion = db.Column(db.String(50), nullable=True)

    # v2.0: institución principal
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id'), nullable=True)

    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_actividad = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    rol = db.Column(db.String(20), default='arqueologo')

    # ── Relaciones v1.0 ───────────────────────────────────────────────────────
    yacimientos = db.relationship('Yacimiento', back_populates='propietario', lazy='dynamic')
    hallazgos = db.relationship('Hallazgo', back_populates='propietario', lazy='dynamic',
                                 foreign_keys='Hallazgo.user_id')
    hallazgos_encontrados = db.relationship('Hallazgo', back_populates='encontrado_por',
                                             lazy='dynamic', foreign_keys='Hallazgo.encontrado_por_id')
    eventos = db.relationship('Evento', back_populates='usuario', lazy='dynamic')
    comentarios = db.relationship('Comentario', back_populates='usuario', lazy='dynamic')
    fases_responsable = db.relationship('FaseProyecto', back_populates='responsable', lazy='dynamic')
    invitaciones_enviadas = db.relationship('Invitacion', back_populates='invitado_por',
                                             lazy='dynamic', foreign_keys='Invitacion.invitado_por_id')
    invitaciones_recibidas = db.relationship('Invitacion', back_populates='invitado',
                                              lazy='dynamic', foreign_keys='Invitacion.invitado_id')

    # ── Relaciones v2.0 ───────────────────────────────────────────────────────
    membresias = db.relationship('UsuarioInstitucion', back_populates='usuario',
                                  cascade='all, delete-orphan', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', back_populates='usuario', lazy='dynamic')

    # ── Relaciones v3.0 ───────────────────────────────────────────────────────
    ues_registradas = db.relationship('UnidadEstratigrafica', back_populates='registrado_por',
                                       lazy='dynamic')
    muestras_recogidas = db.relationship('Muestra', back_populates='recogida_por', lazy='dynamic')

    # ── Métodos ───────────────────────────────────────────────────────────────
    def set_password(self, password: str):
        self.contraseña = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.contraseña, password)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellidos}"

    def has_permission(self, yacimiento_id: int, permission: str):
        from app.models.yacimiento import Yacimiento
        from app.models.invitacion import Invitacion
        yacimiento = Yacimiento.query.get(yacimiento_id)
        if not yacimiento:
            return False, None
        if self.id == yacimiento.user_id:
            return True, 'propietario'
        inv = Invitacion.query.filter_by(
            yacimiento_id=yacimiento_id, invitado_id=self.id, estado='aceptada'
        ).first()
        if not inv:
            return False, None
        return tiene_permiso_rol(inv.rol, permission), inv.rol

    def get_rol_institucional(self, institucion_id: int):
        """Retorna el rol del usuario en una institución."""
        from app.models.institucion import UsuarioInstitucion
        membresia = UsuarioInstitucion.query.filter_by(
            usuario_id=self.id, institucion_id=institucion_id, activo=True
        ).first()
        return membresia.rol_institucional if membresia else None

    def to_dict(self):
        return {
            'id': self.id,
            'nombre_usuario': self.nombre_usuario,
            'email': self.email,
            'nombre': self.nombre,
            'apellidos': self.apellidos,
            'nombre_completo': self.nombre_completo,
            'ocupacion': self.ocupacion,
            'institucion_id': self.institucion_id,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'activo': self.activo,
            'rol': self.rol,
        }

    def __repr__(self):
        return f'<Usuario {self.nombre_usuario}>'
