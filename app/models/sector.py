"""
Modelo de Sector para ArqueoTrack 2.0.
"""

from datetime import datetime
from app import db


class Sector(db.Model):
    """Sector geoespacial dentro de un yacimiento."""

    __tablename__ = 'sectores'

    id = db.Column(db.Integer, primary_key=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id'), nullable=False, index=True)

    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    color = db.Column(db.String(20), default='#6366F1')

    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    polygon_geojson = db.Column(db.Text)
    area = db.Column(db.Float)

    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    yacimiento = db.relationship('Yacimiento', back_populates='sectores')
    hallazgos = db.relationship('Hallazgo', back_populates='sector', cascade='all, delete-orphan', lazy='dynamic')
    eventos = db.relationship('Evento', back_populates='sector', lazy='dynamic')

    # v3.0 — Unidades Estratigráficas
    unidades_estratigraficas = db.relationship('UnidadEstratigrafica', back_populates='sector',
                                                lazy='dynamic')

    __table_args__ = (
        db.Index('idx_sectores_yacimiento', 'yacimiento_id'),
    )

    @property
    def total_hallazgos(self) -> int:
        return self.hallazgos.count()

    def to_dict(self, include_relations: bool = False) -> dict:
        data = {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'color': self.color,
            'lat': self.lat,
            'lng': self.lng,
            'area': self.area,
            'yacimiento_id': self.yacimiento_id,
            'fecha_creacion': self.fecha_creacion.isoformat(),
        }
        if include_relations:
            data['total_hallazgos'] = self.total_hallazgos
        return data

    def __repr__(self):
        return f'<Sector {self.nombre}>'
