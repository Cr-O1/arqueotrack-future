"""
Modelo de Evento (timeline) para ArqueoTrack 2.0.
"""

from datetime import datetime
from app import db


class Evento(db.Model):
    """Evento en la línea de tiempo de un yacimiento."""

    __tablename__ = 'eventos'

    id = db.Column(db.Integer, primary_key=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id'), nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fase_id = db.Column(db.Integer, db.ForeignKey('fases_proyecto.id'))
    hallazgo_id = db.Column(db.Integer, db.ForeignKey('hallazgos.id'))
    sector_id = db.Column(db.Integer, db.ForeignKey('sectores.id'))

    tipo = db.Column(db.String(50), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    ubicacion = db.Column(db.String(200))
    participantes = db.Column(db.Text)
    resultados = db.Column(db.Text)
    prioridad = db.Column(db.String(20), default='media')
    estado_evento = db.Column(db.String(20), default='pendiente')

    # Relaciones
    yacimiento = db.relationship('Yacimiento', back_populates='eventos')
    usuario = db.relationship('Usuario', back_populates='eventos')
    fase = db.relationship('FaseProyecto', back_populates='eventos')
    hallazgo = db.relationship('Hallazgo', back_populates='eventos')
    sector = db.relationship('Sector', back_populates='eventos')

    __table_args__ = (
        db.Index('idx_eventos_yacimiento_fecha', 'yacimiento_id', 'fecha'),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'tipo': self.tipo,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'fecha': self.fecha.isoformat(),
            'prioridad': self.prioridad,
            'estado_evento': self.estado_evento,
            'yacimiento_id': self.yacimiento_id,
        }

    def __repr__(self):
        return f'<Evento {self.titulo}>'
