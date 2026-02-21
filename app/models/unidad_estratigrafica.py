"""
Modelo de Unidad Estratigráfica (UE) y Relaciones — ArqueoTrack 2.0 (v3.0)
"""
from datetime import datetime
from app import db


class RelacionUE(db.Model):
    """
    Relación estratigráfica entre dos UEs (base de la Matriz de Harris).
    ue_posterior (más reciente) → CUBRE / CORTA A → ue_anterior (más antigua)
    """
    __tablename__ = 'relaciones_ue'

    id = db.Column(db.Integer, primary_key=True)
    ue_posterior_id = db.Column(db.Integer, db.ForeignKey('unidades_estratigraficas.id',
                                  ondelete='CASCADE'), nullable=False, index=True)
    ue_anterior_id = db.Column(db.Integer, db.ForeignKey('unidades_estratigraficas.id',
                                 ondelete='CASCADE'), nullable=False, index=True)

    tipo_relacion = db.Column(db.String(30), default='cubre')
    # cubre | corta | rellena | igual_a | se_apoya_en | interfaz_de

    confirmada = db.Column(db.Boolean, default=False)
    notas = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    ue_posterior = db.relationship('UnidadEstratigrafica', foreign_keys=[ue_posterior_id],
                                    back_populates='relaciones_como_posterior')
    ue_anterior = db.relationship('UnidadEstratigrafica', foreign_keys=[ue_anterior_id],
                                   back_populates='relaciones_como_anterior')

    __table_args__ = (
        db.UniqueConstraint('ue_posterior_id', 'ue_anterior_id', name='uq_relacion_ue'),
        db.Index('idx_relacion_ue_posterior', 'ue_posterior_id'),
        db.Index('idx_relacion_ue_anterior', 'ue_anterior_id'),
    )

    def __repr__(self):
        return f'<RelacionUE UE#{self.ue_posterior_id} {self.tipo_relacion} UE#{self.ue_anterior_id}>'


class UnidadEstratigrafica(db.Model):
    """
    Unidad Estratigráfica (UE) — unidad mínima de registro.
    Tipos: depósito | interfaz | corte | estructura | otro
    """
    __tablename__ = 'unidades_estratigraficas'

    id = db.Column(db.Integer, primary_key=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id', ondelete='CASCADE'),
                               nullable=False, index=True)
    sector_id = db.Column(db.Integer, db.ForeignKey('sectores.id'), index=True)
    campana_id = db.Column(db.Integer, db.ForeignKey('campanas.id'), index=True)
    registrado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    numero_ue = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(30), default='deposito')

    descripcion = db.Column(db.Text)
    interpretacion = db.Column(db.Text)

    # Atributos sedimentarios
    color_munsell = db.Column(db.String(30))   # Ej: "10YR 5/3"
    textura = db.Column(db.String(100))         # Ej: "arcillosa", "limosa"
    compactacion = db.Column(db.String(50))     # Ej: "suelta", "compacta"
    composicion = db.Column(db.Text)            # Componentes secundarios

    # Dimensiones y cotas
    cota_superior = db.Column(db.Float)         # metros sobre referencia
    cota_inferior = db.Column(db.Float)
    area_m2 = db.Column(db.Float)
    potencia_cm = db.Column(db.Float)           # espesor en cm

    # Geometría
    polygon_geojson = db.Column(db.Text)

    # Estado
    excavada = db.Column(db.Boolean, default=False)
    fecha_inicio_excavacion = db.Column(db.Date)
    fecha_fin_excavacion = db.Column(db.Date)

    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relaciones ────────────────────────────────────────────────────────────
    yacimiento = db.relationship('Yacimiento', back_populates='unidades_estratigraficas')
    sector = db.relationship('Sector')
    campana = db.relationship('Campana', back_populates='unidades_estratigraficas')
    registrado_por = db.relationship('Usuario', back_populates='ues_registradas')

    relaciones_como_posterior = db.relationship(
        'RelacionUE', foreign_keys='RelacionUE.ue_posterior_id',
        back_populates='ue_posterior', cascade='all, delete-orphan', lazy='dynamic'
    )
    relaciones_como_anterior = db.relationship(
        'RelacionUE', foreign_keys='RelacionUE.ue_anterior_id',
        back_populates='ue_anterior', lazy='dynamic'
    )

    hallazgos = db.relationship('Hallazgo', back_populates='unidad_estratigrafica', lazy='dynamic')
    muestras = db.relationship('Muestra', back_populates='ue', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('yacimiento_id', 'numero_ue', name='uq_ue_yacimiento_numero'),
        db.Index('idx_ue_yacimiento', 'yacimiento_id'),
        db.Index('idx_ue_sector', 'sector_id'),
        db.Index('idx_ue_campana', 'campana_id'),
    )

    @property
    def total_hallazgos(self):
        return self.hallazgos.count()

    @property
    def total_muestras(self):
        return self.muestras.count()

    @property
    def anteriores(self):
        """UEs más antiguas que esta (directas)."""
        return [r.ue_anterior for r in self.relaciones_como_posterior.all()]

    @property
    def posteriores(self):
        """UEs más recientes que esta (directas)."""
        return [r.ue_posterior for r in self.relaciones_como_anterior.all()]

    def to_dict(self, include_relations=False):
        data = {
            'id': self.id, 'numero_ue': self.numero_ue, 'tipo': self.tipo,
            'descripcion': self.descripcion, 'interpretacion': self.interpretacion,
            'color_munsell': self.color_munsell, 'textura': self.textura,
            'cota_superior': self.cota_superior, 'cota_inferior': self.cota_inferior,
            'area_m2': self.area_m2, 'potencia_cm': self.potencia_cm,
            'excavada': self.excavada, 'yacimiento_id': self.yacimiento_id,
            'sector_id': self.sector_id, 'campana_id': self.campana_id,
        }
        if include_relations:
            data.update({
                'total_hallazgos': self.total_hallazgos,
                'total_muestras': self.total_muestras,
                'ids_anteriores': [r.ue_anterior_id for r in self.relaciones_como_posterior.all()],
                'ids_posteriores': [r.ue_posterior_id for r in self.relaciones_como_anterior.all()],
            })
        return data

    def __repr__(self):
        return f'<UE #{self.numero_ue} [{self.tipo}]>'
