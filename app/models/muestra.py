"""
Modelos de Muestra y ResultadoAnalisis — ArqueoTrack 2.0 (v3.0)
"""
from datetime import datetime
from app import db
from app.utils.codes import generar_codigo_unico


class Muestra(db.Model):
    """Muestra de laboratorio tomada de un hallazgo o UE."""
    __tablename__ = 'muestras'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False,
                        default=lambda: 'M-' + generar_codigo_unico(8))

    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id', ondelete='CASCADE'),
                               nullable=False, index=True)
    hallazgo_id = db.Column(db.Integer, db.ForeignKey('hallazgos.id'), index=True)
    ue_id = db.Column(db.Integer, db.ForeignKey('unidades_estratigraficas.id'), index=True)
    campana_id = db.Column(db.Integer, db.ForeignKey('campanas.id'), index=True)
    recogida_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    tipo = db.Column(db.String(50), nullable=False)
    # c14 | palinologia | antracologia | ceramica | metalurgia | fito | zoo | sedimento | otro

    descripcion = db.Column(db.Text)
    cantidad = db.Column(db.String(50))
    peso_gramos = db.Column(db.Float)
    contenedor = db.Column(db.String(100))

    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    cota = db.Column(db.Float)
    contexto_extraccion = db.Column(db.Text)

    fecha_recogida = db.Column(db.DateTime)
    condiciones_almacenamiento = db.Column(db.String(200))

    laboratorio = db.Column(db.String(200))
    numero_laboratorio = db.Column(db.String(100))
    fecha_envio_laboratorio = db.Column(db.DateTime)
    fecha_recepcion_resultados = db.Column(db.DateTime)

    estado = db.Column(db.String(20), default='recogida')
    # recogida | en_laboratorio | resultado_disponible | publicada | descartada

    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    yacimiento = db.relationship('Yacimiento', back_populates='muestras')
    hallazgo = db.relationship('Hallazgo', back_populates='muestras')
    ue = db.relationship('UnidadEstratigrafica', back_populates='muestras')
    campana = db.relationship('Campana')
    recogida_por = db.relationship('Usuario', back_populates='muestras_recogidas')
    resultados = db.relationship('ResultadoAnalisis', back_populates='muestra',
                                  cascade='all, delete-orphan', lazy='dynamic',
                                  order_by='ResultadoAnalisis.fecha_resultado.desc()')

    __table_args__ = (
        db.Index('idx_muestras_yacimiento', 'yacimiento_id'),
        db.Index('idx_muestras_ue', 'ue_id'),
    )

    @property
    def fecha_envio(self):
        return self.fecha_envio_laboratorio

    @property
    def tiene_resultado(self):
        return self.resultados.count() > 0

    def to_dict(self):
        return {
            'id': self.id, 'codigo': self.codigo, 'tipo': self.tipo,
            'descripcion': self.descripcion, 'estado': self.estado,
            'laboratorio': self.laboratorio,
            'fecha_recogida': self.fecha_recogida.isoformat() if self.fecha_recogida else None,
            'yacimiento_id': self.yacimiento_id, 'hallazgo_id': self.hallazgo_id,
            'ue_id': self.ue_id, 'campana_id': self.campana_id,
        }

    def __repr__(self):
        return f'<Muestra {self.codigo} [{self.tipo}]>'


class ResultadoAnalisis(db.Model):
    """Resultado de un análisis de laboratorio sobre una muestra."""
    __tablename__ = 'resultados_analisis'

    id = db.Column(db.Integer, primary_key=True)
    muestra_id = db.Column(db.Integer, db.ForeignKey('muestras.id', ondelete='CASCADE'),
                            nullable=False, index=True)

    # Identificación del resultado
    tipo_analisis = db.Column(db.String(50), nullable=False)
    # c14 | palinologico | antracologico | ceramico | xrf | sem | otro

    # Datos cuantitativos
    valor_principal = db.Column(db.String(200))
    # Para C14: "2350 ± 40 BP" | Para XRF: "Fe: 62.3%, Sn: 5.1%"
    margen_error = db.Column(db.String(100))
    calibrado_calbc = db.Column(db.String(200))  # Rango calibrado calendario

    # Descripción
    descripcion = db.Column(db.Text)
    interpretacion = db.Column(db.Text)
    referencias = db.Column(db.Text)

    # Laboratorio
    laboratorio = db.Column(db.String(200))
    tecnico = db.Column(db.String(200))
    metodo = db.Column(db.String(200))
    fecha_resultado = db.Column(db.DateTime, default=datetime.utcnow)

    # Archivos
    archivo_url = db.Column(db.String(500))  # PDF o CSV del resultado
    datos_json = db.Column(db.Text)  # Datos brutos del laboratorio en JSON

    # Revisión científica
    revisado = db.Column(db.Boolean, default=False)
    revisor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_revision = db.Column(db.DateTime)

    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    muestra = db.relationship('Muestra', back_populates='resultados')
    revisor = db.relationship('Usuario', foreign_keys=[revisor_id])

    def to_dict(self):
        return {
            'id': self.id, 'muestra_id': self.muestra_id,
            'tipo_analisis': self.tipo_analisis,
            'valor_principal': self.valor_principal,
            'margen_error': self.margen_error,
            'calibrado_calbc': self.calibrado_calbc,
            'descripcion': self.descripcion,
            'interpretacion': self.interpretacion,
            'laboratorio': self.laboratorio,
            'fecha_resultado': self.fecha_resultado.isoformat() if self.fecha_resultado else None,
            'revisado': self.revisado,
        }

    def __repr__(self):
        return f'<ResultadoAnalisis {self.tipo_analisis} muestra={self.muestra_id}>'
