"""
Modelo de Fase de Proyecto para ArqueoTrack 2.0.
"""

from datetime import datetime
from app import db


class FaseProyecto(db.Model):
    """Fase temporal de un proyecto arqueológico."""

    __tablename__ = 'fases_proyecto'

    id = db.Column(db.Integer, primary_key=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id'), nullable=False, index=True)
    responsable_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(20), default='planificada')  # planificada | en_curso | finalizada
    orden = db.Column(db.Integer, default=0)

    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)

    objetivos = db.Column(db.Text)
    metodologia = db.Column(db.Text)
    recursos_necesarios = db.Column(db.Text)
    resultados_esperados = db.Column(db.Text)
    presupuesto = db.Column(db.Float)
    equipo_participante = db.Column(db.Text)
    notas = db.Column(db.Text)

    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    yacimiento = db.relationship('Yacimiento', back_populates='fases')
    responsable = db.relationship('Usuario', back_populates='fases_responsable')
    eventos = db.relationship('Evento', back_populates='fase', lazy='dynamic')

    __table_args__ = (
        db.Index('idx_fases_yacimiento', 'yacimiento_id'),
    )

    def __repr__(self):
        return f'<FaseProyecto {self.nombre}>'
