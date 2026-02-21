"""
Modelo de Campaña Arqueológica para ArqueoTrack 2.0 (v2.0).
Una campaña representa una temporada de excavación dentro de un yacimiento.
"""

from datetime import datetime
from app import db


# ── Tabla de asociación Campaña ↔ Equipo ──────────────────────────────────────
campana_equipo = db.Table(
    'campana_equipo',
    db.Column('campana_id', db.Integer, db.ForeignKey('campanas.id', ondelete='CASCADE'),
               primary_key=True),
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'),
               primary_key=True),
    db.Column('rol_en_campana', db.String(50), default='tecnico_campo'),
    db.Column('fecha_incorporacion', db.DateTime, default=datetime.utcnow),
)


class Campana(db.Model):
    """
    Campaña de excavación arqueológica.
    Agrupa hallazgos y actividades de una temporada específica dentro de un yacimiento.
    """

    __tablename__ = 'campanas'

    id = db.Column(db.Integer, primary_key=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id', ondelete='CASCADE'),
                               nullable=False, index=True)
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id'), index=True)
    director_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), index=True)

    # Identificación
    nombre = db.Column(db.String(200), nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    codigo = db.Column(db.String(20))  # Código interno ej: "CAM-2024-01"

    # Temporalidad
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)

    # Descripción científica
    objetivos = db.Column(db.Text)
    metodologia = db.Column(db.Text)
    resultados = db.Column(db.Text)
    conclusiones = db.Column(db.Text)

    # Financiación
    presupuesto = db.Column(db.Float)
    financiador = db.Column(db.String(200))
    numero_expediente = db.Column(db.String(100))

    # Estado
    estado = db.Column(db.String(20), default='planificada')
    # planificada | en_curso | finalizada | publicada

    # Metadata
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    yacimiento = db.relationship('Yacimiento', back_populates='campanas')
    institucion = db.relationship('Institucion', back_populates='campanas')
    director = db.relationship('Usuario', foreign_keys=[director_id])

    equipo = db.relationship(
        'Usuario',
        secondary=campana_equipo,
        lazy='dynamic',
    )

    hallazgos = db.relationship('Hallazgo', back_populates='campana', lazy='dynamic')
    unidades_estratigraficas = db.relationship('UnidadEstratigrafica', back_populates='campana',
                                                lazy='dynamic')

    __table_args__ = (
        db.Index('idx_campanas_yacimiento_anio', 'yacimiento_id', 'anio'),
        db.UniqueConstraint('yacimiento_id', 'anio', 'nombre', name='uq_campana_yacimiento_anio_nombre'),
    )

    # ── Propiedades ────────────────────────────────────────────────────────────

    @property
    def esta_activa(self) -> bool:
        return self.estado == 'en_curso'

    @property
    def total_hallazgos(self) -> int:
        return self.hallazgos.count()

    @property
    def total_ues(self) -> int:
        return self.unidades_estratigraficas.count()

    @property
    def duracion_dias(self) -> int:
        if self.fecha_inicio and self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).days
        return 0

    def to_dict(self, include_stats: bool = False) -> dict:
        data = {
            'id': self.id,
            'nombre': self.nombre,
            'anio': self.anio,
            'codigo': self.codigo,
            'yacimiento_id': self.yacimiento_id,
            'estado': self.estado,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'objetivos': self.objetivos,
            'presupuesto': self.presupuesto,
            'financiador': self.financiador,
        }
        if include_stats:
            data.update({
                'total_hallazgos': self.total_hallazgos,
                'total_ues': self.total_ues,
                'duracion_dias': self.duracion_dias,
            })
        return data

    def __repr__(self):
        return f'<Campana {self.nombre} ({self.anio})>'
