"""
Formularios WTForms para ArqueoTrack 2.0.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, DateField, SelectField,
    TextAreaField, FloatField, DateTimeField, BooleanField, FileField,
    IntegerField,
)
from wtforms.validators import InputRequired, Length, Email, EqualTo, ValidationError, Optional, DataRequired, URL

from app.utils.constants import (
    ESTADOS_CONSERVACION,
    FASES_PREDEFINIDAS,
    OCUPACIONES,
    TIPOS_EVENTO,
    TIPOS_HALLAZGO,
)


class RegistroForm(FlaskForm):
    nombre_usuario = StringField('Nombre de Usuario', validators=[InputRequired(), Length(min=4, max=20)])
    nombre = StringField('Nombre', validators=[InputRequired(), Length(max=100)])
    apellidos = StringField('Apellidos', validators=[InputRequired(), Length(max=100)])
    correo_electronico = StringField('Correo Electrónico', validators=[InputRequired(), Email(), Length(max=120)])
    fecha_nacimiento = DateField('Fecha de Nacimiento', validators=[InputRequired()])
    ocupacion = SelectField('Ocupación', choices=OCUPACIONES, validators=[Optional()])
    contraseña = PasswordField('Contraseña', validators=[InputRequired(), Length(min=10)])
    confirmar_contraseña = PasswordField('Confirmar Contraseña', validators=[InputRequired(), EqualTo('contraseña')])
    enviar = SubmitField('Registrarse')

    def validate_nombre_usuario(self, nombre_usuario):
        from app.models.user import Usuario
        if Usuario.query.filter_by(nombre_usuario=nombre_usuario.data).first():
            raise ValidationError('Nombre de usuario ya existe.')

    def validate_correo_electronico(self, correo_electronico):
        from app.models.user import Usuario
        if Usuario.query.filter_by(email=correo_electronico.data).first():
            raise ValidationError('Correo electrónico ya registrado.')


class LoginForm(FlaskForm):
    correo_electronico = StringField('Correo Electrónico', validators=[InputRequired(), Email()])
    contraseña = PasswordField('Contraseña', validators=[InputRequired()])
    enviar = SubmitField('Iniciar Sesión')


class YacimientoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[InputRequired()])
    ubicacion = StringField('Ubicación')
    descripcion = TextAreaField('Descripción')
    fecha_inicio = DateField('Fecha Inicio', validators=[Optional()])
    fecha_fin = DateField('Fecha Fin', validators=[Optional()])
    altitud_media = FloatField('Altitud Media (m)', validators=[Optional()])
    lat = FloatField('Latitud', validators=[Optional()])
    lng = FloatField('Longitud', validators=[Optional()])
    polygon_geojson = TextAreaField('GeoJSON Polígono', validators=[Optional()])
    area = FloatField('Área (m²)', validators=[Optional()])
    responsable = StringField('Responsable', validators=[Optional()])
    submit = SubmitField('Guardar')


class EditarProcesoYacimientoForm(FlaskForm):
    responsable = StringField('Responsable')
    fecha_inicio = DateField('Fecha Inicio', validators=[Optional()])
    fecha_fin = DateField('Fecha Fin', validators=[Optional()])
    esta_activo = BooleanField('Activo')
    submit = SubmitField('Guardar')


class HallazgoForm(FlaskForm):
    tipo = SelectField('Tipo', choices=TIPOS_HALLAZGO, validators=[InputRequired()])
    material = StringField('Material')
    datacion = StringField('Datación')
    dimensiones = StringField('Dimensiones')
    peso = FloatField('Peso (g)', validators=[Optional()])
    estado_conservacion = SelectField('Estado Conservación', choices=ESTADOS_CONSERVACION)
    proceso_extraccion = TextAreaField('Proceso de Extracción', validators=[Optional()], render_kw={'rows': 4})
    destino = StringField('Destino/Repositorio', validators=[Optional()])
    descripcion = TextAreaField('Descripción')
    lat = FloatField('Latitud', validators=[Optional()])
    lng = FloatField('Longitud', validators=[Optional()])
    fecha = DateField('Fecha Hallazgo', validators=[Optional()])
    notas = TextAreaField('Notas', validators=[Optional()], render_kw={'rows': 3})
    sector_id = SelectField('Sector', coerce=int)
    foto = FileField('Foto')
    ubicacion = StringField('Ubicación/Referencia', validators=[Optional(), Length(max=200)])
    altitud = FloatField('Altitud (m s.n.m.)', validators=[Optional()])
    submit = SubmitField('Guardar')


class SectorForm(FlaskForm):
    nombre = StringField('Nombre', validators=[InputRequired()])
    descripcion = TextAreaField('Descripción')
    color = StringField('Color', default='#6366F1')
    lat = FloatField('Latitud', validators=[Optional()])
    lng = FloatField('Longitud', validators=[Optional()])
    polygon_geojson = TextAreaField('GeoJSON Polígono', validators=[Optional()])
    area = FloatField('Área (m²)', validators=[Optional()])
    submit = SubmitField('Guardar')


class FaseForm(FlaskForm):
    nombre = SelectField('Nombre', choices=FASES_PREDEFINIDAS, validators=[InputRequired()])
    descripcion = TextAreaField('Descripción')
    estado = SelectField('Estado', choices=[('planificada', 'Planificada'), ('en_curso', 'En Curso'), ('finalizada', 'Finalizada')])
    fecha_inicio = DateField('Fecha Inicio', validators=[Optional()])
    fecha_fin = DateField('Fecha Fin', validators=[Optional()])
    objetivos = TextAreaField('Objetivos', validators=[Optional()], render_kw={'rows': 3})
    metodologia = TextAreaField('Metodología', validators=[Optional()], render_kw={'rows': 3})
    recursos_necesarios = TextAreaField('Recursos Necesarios', validators=[Optional()], render_kw={'rows': 3})
    resultados_esperados = TextAreaField('Resultados Esperados', validators=[Optional()], render_kw={'rows': 3})
    presupuesto = FloatField('Presupuesto', validators=[Optional()])
    equipo_participante = TextAreaField('Equipo Participante', validators=[Optional()], render_kw={'rows': 3})
    notas = TextAreaField('Notas', validators=[Optional()], render_kw={'rows': 3})
    submit = SubmitField('Guardar')


class EventoForm(FlaskForm):
    tipo = SelectField('Tipo', choices=TIPOS_EVENTO)
    titulo = StringField('Título', validators=[InputRequired()])
    descripcion = TextAreaField('Descripción', validators=[InputRequired()])
    fecha = DateTimeField('Fecha', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    fase_id = SelectField('Fase', coerce=int)
    hallazgo_id = SelectField('Hallazgo', coerce=int)
    sector_id = SelectField('Sector', coerce=int)
    prioridad = SelectField('Prioridad', choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('urgente', 'Urgente')])
    estado_evento = SelectField('Estado', choices=[('pendiente', 'Pendiente'), ('en_progreso', 'En Progreso'), ('completado', 'Completado'), ('cancelado', 'Cancelado')])
    participantes = TextAreaField('Participantes', validators=[Optional()], render_kw={'rows': 3})
    resultados = TextAreaField('Resultados', validators=[Optional()], render_kw={'rows': 3})
    submit = SubmitField('Guardar')


class InvitacionForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    rol = SelectField('Rol', choices=[
        ('visualizador', 'Visualizador'),
        ('editor', 'Editor'),
        ('colaborador', 'Colaborador'),
        ('asistente', 'Asistente'),
    ])
    mensaje = TextAreaField('Mensaje')
    submit = SubmitField('Enviar')


class BuscarCodigoForm(FlaskForm):
    codigo = StringField('Código', validators=[InputRequired(), Length(min=10, max=10)])
    submit = SubmitField('Buscar')


# ─── v2.0 Instituciones ────────────────────────────────────────────────────────

class InstitucionForm(FlaskForm):
    nombre = StringField('Nombre de la institución', validators=[InputRequired(), Length(max=200)])
    tipo = SelectField('Tipo', choices=[
        ('universidad', 'Universidad'),
        ('museo', 'Museo'),
        ('empresa', 'Empresa de Arqueología'),
        ('ong', 'ONG / Fundación'),
        ('gobierno', 'Organismo Gubernamental'),
        ('investigacion', 'Centro de Investigación'),
        ('otro', 'Otro'),
    ])
    descripcion = TextAreaField('Descripción', validators=[Optional()], render_kw={'rows': 4})
    pais = SelectField('País', choices=[
        ('ES', 'España'), ('FR', 'Francia'), ('PT', 'Portugal'), ('IT', 'Italia'),
        ('DE', 'Alemania'), ('GB', 'Reino Unido'), ('MX', 'México'), ('AR', 'Argentina'),
        ('PE', 'Perú'), ('CO', 'Colombia'), ('CL', 'Chile'), ('GR', 'Grecia'),
        ('EG', 'Egipto'), ('TR', 'Turquía'), ('JO', 'Jordania'), ('MA', 'Marruecos'),
        ('', 'Otro'),
    ], validators=[Optional()])
    ciudad = StringField('Ciudad', validators=[Optional(), Length(max=100)])
    web = StringField('Sitio web', validators=[Optional(), URL(), Length(max=300)])
    email_contacto = StringField('Email de contacto', validators=[Optional(), Email()])
    submit = SubmitField('Guardar')


class UnirseInstitucionForm(FlaskForm):
    codigo_invitacion = StringField('Código de invitación', validators=[InputRequired(), Length(max=50)])
    submit = SubmitField('Unirse')


class AñadirMiembroForm(FlaskForm):
    email = StringField('Email del usuario', validators=[InputRequired(), Email()])
    rol = SelectField('Rol institucional', choices=[
        ('director_proyecto', 'Director/a de Proyecto'),
        ('arqueologo_senior', 'Arqueólogo/a Senior'),
        ('arqueologo_junior', 'Arqueólogo/a Junior'),
        ('tecnico_campo', 'Técnico/a de Campo'),
        ('restaurador', 'Restaurador/a'),
        ('investigador_externo', 'Investigador/a Externo'),
        ('estudiante', 'Estudiante'),
    ])
    submit = SubmitField('Añadir miembro')


# ─── v2.0 Campañas ─────────────────────────────────────────────────────────────

class CampanaForm(FlaskForm):
    nombre = StringField('Nombre de la campaña', validators=[InputRequired(), Length(max=200)])
    anio = IntegerField('Año', validators=[DataRequired()])
    codigo = StringField('Código', validators=[Optional(), Length(max=20)])
    fecha_inicio = DateField('Fecha de inicio', validators=[Optional()])
    fecha_fin = DateField('Fecha de fin', validators=[Optional()])
    objetivos = TextAreaField('Objetivos', validators=[Optional()], render_kw={'rows': 4})
    metodologia = TextAreaField('Metodología', validators=[Optional()], render_kw={'rows': 4})
    presupuesto = FloatField('Presupuesto (€)', validators=[Optional()])
    financiador = StringField('Financiador', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Guardar')


# ─── v3.0 Unidades Estratigráficas ─────────────────────────────────────────────

class UnidadEstratigraficaForm(FlaskForm):
    numero_ue = IntegerField('Número UE', validators=[Optional()])
    tipo = SelectField('Tipo', choices=[
        ('deposito', 'Depósito'),
        ('interfaz', 'Interfaz'),
        ('corte', 'Corte'),
        ('estructura', 'Estructura'),
        ('otro', 'Otro'),
    ])
    descripcion = TextAreaField('Descripción', validators=[Optional()], render_kw={'rows': 4})
    interpretacion = TextAreaField('Interpretación', validators=[Optional()], render_kw={'rows': 3})
    color_munsell = StringField('Color Munsell', validators=[Optional(), Length(max=30)])
    textura = StringField('Textura', validators=[Optional(), Length(max=100)])
    compactacion = SelectField('Compactación', choices=[
        ('', 'Selecciona...'),
        ('suelta', 'Suelta'),
        ('friable', 'Friable'),
        ('compacta', 'Compacta'),
        ('muy_compacta', 'Muy compacta'),
        ('cementada', 'Cementada'),
    ], validators=[Optional()])
    composicion = TextAreaField('Composición', validators=[Optional()], render_kw={'rows': 2})
    cota_superior = FloatField('Cota superior (m)', validators=[Optional()])
    cota_inferior = FloatField('Cota inferior (m)', validators=[Optional()])
    area_m2 = FloatField('Área (m²)', validators=[Optional()])
    campana_id = SelectField('Campaña', coerce=int, validators=[Optional()])
    sector_id = SelectField('Sector', coerce=int, validators=[Optional()])
    submit = SubmitField('Guardar')


class RelacionUEForm(FlaskForm):
    ue_anterior_id = SelectField('UE anterior (más antigua)', coerce=int, validators=[DataRequired()])
    tipo_relacion = SelectField('Tipo de relación', choices=[
        ('cubre', 'Cubre'),
        ('corta', 'Corta'),
        ('rellena', 'Rellena'),
        ('igual_a', 'Igual a'),
        ('se_apoya_en', 'Se apoya en'),
        ('interfaz_de', 'Es interfaz de'),
    ])
    notas = TextAreaField('Notas', validators=[Optional()], render_kw={'rows': 2})
    confirmada = BooleanField('Relación confirmada')
    submit = SubmitField('Añadir relación')


# ─── v3.0 Muestras ─────────────────────────────────────────────────────────────

class MuestraForm(FlaskForm):
    tipo = SelectField('Tipo de muestra', choices=[
        ('c14', 'Carbono-14 (C14)'),
        ('palinologia', 'Palinología'),
        ('antracologia', 'Antracología'),
        ('ceramica', 'Análisis Cerámico'),
        ('metalurgia', 'Análisis Metalúrgico'),
        ('fito', 'Fitolitos'),
        ('zoo', 'Zooarqueología'),
        ('sedimento', 'Análisis de Sedimento'),
        ('adn', 'ADN Antiguo'),
        ('isotopos', 'Isótopos Estables'),
        ('otro', 'Otro'),
    ])
    descripcion = TextAreaField('Descripción', validators=[Optional()], render_kw={'rows': 3})
    cantidad = IntegerField('Cantidad', validators=[Optional()])
    peso_gramos = FloatField('Peso (g)', validators=[Optional()])
    contenedor = StringField('Tipo de contenedor', validators=[Optional(), Length(max=100)])
    latitud = FloatField('Latitud', validators=[Optional()])
    longitud = FloatField('Longitud', validators=[Optional()])
    cota = FloatField('Cota (m)', validators=[Optional()])
    contexto_extraccion = TextAreaField('Contexto de extracción', validators=[Optional()], render_kw={'rows': 3})
    fecha_recogida = DateField('Fecha de recogida', validators=[Optional()])
    condiciones_almacenamiento = TextAreaField('Condiciones de almacenamiento', validators=[Optional()], render_kw={'rows': 2})
    ue_id = SelectField('Unidad estratigráfica', coerce=int, validators=[Optional()])
    hallazgo_id = SelectField('Hallazgo asociado', coerce=int, validators=[Optional()])
    campana_id = SelectField('Campaña', coerce=int, validators=[Optional()])
    submit = SubmitField('Registrar muestra')


class EnviarLaboratorioForm(FlaskForm):
    laboratorio = StringField('Nombre del laboratorio', validators=[InputRequired(), Length(max=200)])
    numero_laboratorio = StringField('Nº de referencia laboratorio', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Registrar envío')


class ResultadoAnalisisForm(FlaskForm):
    tipo_analisis = SelectField('Tipo de análisis', choices=[
        ('c14', 'Datación C14'),
        ('palinologico', 'Análisis Polínico'),
        ('antracologico', 'Análisis Antracológico'),
        ('ceramico', 'Análisis Cerámico'),
        ('metalurgico', 'Análisis Metalúrgico'),
        ('adn', 'Análisis de ADN'),
        ('isotopos', 'Isótopos Estables'),
        ('otro', 'Otro'),
    ])
    valor_principal = StringField('Valor principal (ej: 1250 BP)', validators=[Optional(), Length(max=100)])
    margen_error = StringField('Margen de error', validators=[Optional(), Length(max=50)])
    descripcion = TextAreaField('Descripción del resultado', validators=[InputRequired()], render_kw={'rows': 4})
    interpretacion = TextAreaField('Interpretación', validators=[Optional()], render_kw={'rows': 3})
    metodo = StringField('Método utilizado', validators=[Optional(), Length(max=200)])
    tecnico = StringField('Técnico responsable', validators=[Optional(), Length(max=200)])
    referencias = TextAreaField('Referencias bibliográficas', validators=[Optional()], render_kw={'rows': 2})
    submit = SubmitField('Registrar resultado')
