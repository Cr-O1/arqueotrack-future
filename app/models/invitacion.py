"""
Modelo de Invitación para ArqueoTrack 2.0.
"""

from datetime import datetime
from app import db


class Invitacion(db.Model):
    """Invitación de colaboración a un yacimiento."""

    __tablename__ = 'invitaciones'

    id = db.Column(db.Integer, primary_key=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id'), nullable=False, index=True)
    invitado_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    invitado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    email = db.Column(db.String(120), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='visualizador')
    mensaje = db.Column(db.Text)

    estado = db.Column(db.String(20), default='pendiente')  # pendiente | aceptada | rechazada
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_respuesta = db.Column(db.DateTime)

    # Relaciones
    yacimiento = db.relationship('Yacimiento', back_populates='invitaciones')
    invitado = db.relationship('Usuario', back_populates='invitaciones_recibidas', foreign_keys=[invitado_id])
    invitado_por = db.relationship('Usuario', back_populates='invitaciones_enviadas', foreign_keys=[invitado_por_id])

    __table_args__ = (
        db.Index('idx_invitaciones_yacimiento_invitado', 'yacimiento_id', 'invitado_id'),
    )

    def __repr__(self):
        return f'<Invitacion {self.email} → Yacimiento {self.yacimiento_id}>'
