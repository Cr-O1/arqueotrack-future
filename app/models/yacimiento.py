"""
Modelo de Yacimiento — ArqueoTrack 2.0 (actualizado para v2.0 + v3.0)
"""
from datetime import datetime
from app import db


class Yacimiento(db.Model):
    __tablename__ = 'yacimientos'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)

    # v2.0: pertenencia institucional
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id'), nullable=True, index=True)

    nombre = db.Column(db.String(200), nullable=False)
    ubicacion = db.Column(db.String(300))
    descripcion = db.Column(db.Text)

    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    polygon_geojson = db.Column(db.Text)
    area_m2 = db.Column(db.Float)
    altitud_media = db.Column(db.Float)

    responsable = db.Column(db.String(100))
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)

    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relaciones v1.0 ───────────────────────────────────────────────────────
    propietario = db.relationship('Usuario', back_populates='yacimientos')
    hallazgos = db.relationship('Hallazgo', back_populates='yacimiento',
                                 cascade='all, delete-orphan', lazy='dynamic')
    sectores = db.relationship('Sector', back_populates='yacimiento',
                                cascade='all, delete-orphan', lazy='dynamic')
    fases = db.relationship('FaseProyecto', back_populates='yacimiento',
                             cascade='all, delete-orphan', lazy='dynamic',
                             order_by='FaseProyecto.orden')
    eventos = db.relationship('Evento', back_populates='yacimiento',
                               cascade='all, delete-orphan', lazy='dynamic',
                               order_by='Evento.fecha.desc()')
    invitaciones = db.relationship('Invitacion', back_populates='yacimiento',
                                    cascade='all, delete-orphan', lazy='dynamic')

    # ── Relaciones v2.0 ───────────────────────────────────────────────────────
    institucion = db.relationship('Institucion', back_populates='yacimientos')
    campanas = db.relationship('Campana', back_populates='yacimiento',
                                cascade='all, delete-orphan', lazy='dynamic',
                                order_by='Campana.anio.desc()')

    # ── Relaciones v3.0 ───────────────────────────────────────────────────────
    unidades_estratigraficas = db.relationship(
        'UnidadEstratigrafica', back_populates='yacimiento',
        cascade='all, delete-orphan', lazy='dynamic',
        order_by='UnidadEstratigrafica.numero_ue'
    )
    muestras = db.relationship('Muestra', back_populates='yacimiento',
                                cascade='all, delete-orphan', lazy='dynamic')

    __table_args__ = (
        db.Index('idx_yacimientos_user_fecha', 'user_id', 'fecha_creacion'),
        db.Index('idx_yacimientos_institucion', 'institucion_id'),
    )

    def __init__(self, **kwargs):
        if 'propietario_id' in kwargs and 'user_id' not in kwargs:
            kwargs['user_id'] = kwargs.pop('propietario_id')

        latitud = kwargs.pop('latitud', None)
        longitud = kwargs.pop('longitud', None)
        if latitud is not None and 'lat' not in kwargs:
            kwargs['lat'] = latitud
        if longitud is not None and 'lng' not in kwargs:
            kwargs['lng'] = longitud

        municipio = kwargs.pop('municipio', None)
        pais = kwargs.pop('pais', None)
        if (municipio or pais) and not kwargs.get('ubicacion'):
            kwargs['ubicacion'] = ', '.join(filter(None, [municipio, pais]))

        # Compatibilidad con argumentos legacy no persistidos en v2/v3
        kwargs.pop('estado', None)

        super().__init__(**kwargs)

    @property
    def esta_activo(self):
        return self.fecha_fin is None

    @property
    def total_hallazgos(self):
        try:
            return self.hallazgos.count()
        except Exception:
            return 0

    @property
    def hallazgos_con_foto(self):
        from app.models.hallazgo import Hallazgo
        return self.hallazgos.filter(Hallazgo.foto.isnot(None), Hallazgo.foto != '').count()

    @property
    def total_sectores(self):
        return self.sectores.count()

    @property
    def total_fases(self):
        return self.fases.count()

    @property
    def total_ues(self):
        return self.unidades_estratigraficas.count()

    @property
    def total_campanas(self):
        return self.campanas.count()

    def obtener_rol_usuario(self, user_id):
        if self.user_id == user_id:
            return 'propietario'
        from app.models.invitacion import Invitacion
        inv = Invitacion.query.filter_by(
            yacimiento_id=self.id, invitado_id=user_id, estado='aceptada'
        ).first()
        return inv.rol if inv else None

    def to_dict(self, include_relations=False):
        data = {
            'id': self.id, 'nombre': self.nombre, 'ubicacion': self.ubicacion,
            'descripcion': self.descripcion, 'lat': self.lat, 'lng': self.lng,
            'area_m2': self.area_m2, 'altitud_media': self.altitud_media,
            'responsable': self.responsable,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'esta_activo': self.esta_activo,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'propietario_id': self.user_id,
            'institucion_id': self.institucion_id,
        }
        if include_relations:
            data.update({
                'total_hallazgos': self.total_hallazgos,
                'total_sectores': self.total_sectores,
                'total_fases': self.total_fases,
                'total_ues': self.total_ues,
                'total_campanas': self.total_campanas,
            })
        return data

    def __repr__(self):
        return f'<Yacimiento {self.nombre}>'
