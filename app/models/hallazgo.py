"""
Modelo de Hallazgo — ArqueoTrack 2.0 (actualizado v2.0 + v3.0)
"""
from datetime import datetime
from app import db


class Hallazgo(db.Model):
    __tablename__ = 'hallazgos'

    id = db.Column(db.Integer, primary_key=True)
    codigo_acceso = db.Column(db.String(10), unique=True, nullable=False, index=True)

    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id'), index=True)
    sector_id = db.Column(db.Integer, db.ForeignKey('sectores.id'), index=True)
    encontrado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    # v2.0: vinculación a campaña
    campana_id = db.Column(db.Integer, db.ForeignKey('campanas.id'), index=True)
    # v3.0: vinculación a UE
    ue_id = db.Column(db.Integer, db.ForeignKey('unidades_estratigraficas.id'), index=True)

    tipo = db.Column(db.String(100))
    material = db.Column(db.String(100))
    datacion = db.Column(db.String(100))
    descripcion = db.Column(db.Text)
    notas = db.Column(db.Text)

    ubicacion = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    altitud = db.Column(db.Float)

    dimensiones = db.Column(db.String(100))
    peso = db.Column(db.Float)
    estado_conservacion = db.Column(db.String(50))

    foto = db.Column(db.String(200))
    fecha = db.Column(db.Date)
    proceso_extraccion = db.Column(db.Text)
    destino = db.Column(db.String(200))

    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relaciones ────────────────────────────────────────────────────────────
    propietario = db.relationship('Usuario', back_populates='hallazgos', foreign_keys=[user_id])
    encontrado_por = db.relationship('Usuario', back_populates='hallazgos_encontrados',
                                      foreign_keys=[encontrado_por_id])
    yacimiento = db.relationship('Yacimiento', back_populates='hallazgos')
    sector = db.relationship('Sector', back_populates='hallazgos')
    comentarios = db.relationship('Comentario', back_populates='hallazgo',
                                   cascade='all, delete-orphan', lazy='dynamic',
                                   order_by='Comentario.fecha_creacion.desc()')
    eventos = db.relationship('Evento', back_populates='hallazgo', lazy='dynamic')

    # v2.0
    campana = db.relationship('Campana', back_populates='hallazgos')
    # v3.0
    unidad_estratigrafica = db.relationship('UnidadEstratigrafica', back_populates='hallazgos')
    muestras = db.relationship('Muestra', back_populates='hallazgo', lazy='dynamic')

    __table_args__ = (
        db.Index('idx_hallazgos_yacimiento_fecha', 'yacimiento_id', 'fecha_registro'),
        db.Index('idx_hallazgos_sector', 'sector_id'),
        db.Index('idx_hallazgos_campana', 'campana_id'),
        db.Index('idx_hallazgos_ue', 'ue_id'),
    )

    def to_dict(self):
        return {
            'id': self.id, 'codigo_acceso': self.codigo_acceso,
            'tipo': self.tipo, 'material': self.material,
            'descripcion': self.descripcion, 'ubicacion': self.ubicacion,
            'lat': self.lat, 'lng': self.lng, 'altitud': self.altitud,
            'estado_conservacion': self.estado_conservacion,
            'foto': self.foto,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'fecha_registro': self.fecha_registro.isoformat(),
            'yacimiento_id': self.yacimiento_id, 'sector_id': self.sector_id,
            'campana_id': self.campana_id, 'ue_id': self.ue_id,
        }

    def __repr__(self):
        return f'<Hallazgo {self.codigo_acceso}>'
