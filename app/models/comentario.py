"""
Modelo de Comentario para ArqueoTrack 2.0.
"""

from datetime import datetime
from app import db


class Comentario(db.Model):
    """Comentario sobre un hallazgo."""

    __tablename__ = 'comentarios'

    id = db.Column(db.Integer, primary_key=True)
    hallazgo_id = db.Column(db.Integer, db.ForeignKey('hallazgos.id'), nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    contenido = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_edicion = db.Column(db.DateTime)

    # Relaciones
    hallazgo = db.relationship('Hallazgo', back_populates='comentarios')
    usuario = db.relationship('Usuario', back_populates='comentarios')

    def __repr__(self):
        return f'<Comentario {self.id} en Hallazgo {self.hallazgo_id}>'
