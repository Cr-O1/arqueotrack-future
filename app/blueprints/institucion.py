"""
Blueprint de Instituciones - ArqueoTrack v2.0
Gestión multi-tenant: CRUD de instituciones y membresías.
"""

import structlog
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.institucion import Institucion, UsuarioInstitucion
from app.models.user import Usuario
from app.forms import InstitucionForm, UnirseInstitucionForm
from app.services.institucion_service import InstitucionService, JERARQUIA_ROLES
from app.services.audit_service import AuditService

log = structlog.get_logger(__name__)
institucion_bp = Blueprint('institucion', __name__)


@institucion_bp.route('/instituciones')
@login_required
def listar():
    """Directorio público de instituciones verificadas."""
    query = request.args.get('q', '')
    tipo = request.args.get('tipo', '')
    pais = request.args.get('pais', '')
    instituciones = InstitucionService.buscar(query, tipo, pais)

    # Instituciones a las que pertenece el usuario
    mis_instituciones = [inst for inst, _ in InstitucionService.get_instituciones_usuario(current_user.id)]

    return render_template(
        'instituciones/listar.html',
        instituciones=instituciones,
        mis_instituciones=mis_instituciones,
        query=query,
        tipo=tipo,
        pais=pais,
    )


@institucion_bp.route('/instituciones/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    """Crear una nueva institución."""
    form = InstitucionForm()
    if form.validate_on_submit():
        try:
            datos = {
                'nombre': form.nombre.data,
                'tipo': form.tipo.data,
                'pais': form.pais.data,
                'ciudad': form.ciudad.data,
                'descripcion': form.descripcion.data,
                'sitio_web': form.sitio_web.data,
            }
            inst = InstitucionService.crear(
                nombre=form.nombre.data,
                tipo=form.tipo.data,
                datos={
                    'pais': form.pais.data,
                    'ciudad': form.ciudad.data,
                    'descripcion': form.descripcion.data,
                    'sitio_web': form.web.data,
                },
                fundador_id=current_user.id
            )
            AuditService.registrar('create', 'institucion', inst.id, datos_nuevos=inst.to_dict())
            flash(f'Institución "{inst.nombre}" creada. Estará disponible públicamente tras la verificación.', 'success')
            return redirect(url_for('institucion.detalle', inst_id=inst.id))
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            log.error("Error al crear institución", error=str(e))
            db.session.rollback()
            flash('Error inesperado al crear la institución.', 'error')
    return render_template('instituciones/nueva.html', formulario=form)


@institucion_bp.route('/institucion/<int:inst_id>')
@login_required
def detalle(inst_id):
    """Detalle de la institución."""
    inst = Institucion.query.get_or_404(inst_id)
    mi_rol = inst.get_rol_usuario(current_user.id)
    es_director = mi_rol == 'director_general'

    miembros = (
        UsuarioInstitucion.query
        .filter_by(institucion_id=inst_id, activo=True)
        .order_by(UsuarioInstitucion.rol_institucional)
        .all()
    )
    return render_template(
        'instituciones/detalle.html',
        institucion=inst,
        mi_rol=mi_rol,
        es_director=es_director,
        miembros=miembros,
        roles=JERARQUIA_ROLES,
    )


@institucion_bp.route('/institucion/<int:inst_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(inst_id):
    """Editar información de la institución (solo director_general)."""
    inst = Institucion.query.get_or_404(inst_id)
    if not InstitucionService.tiene_permiso(inst, current_user.id, 'manage'):
        abort(403)

    form = InstitucionForm(obj=inst)
    if form.validate_on_submit():
        datos_anteriores = inst.to_dict()
        try:
            datos = {
                'nombre': form.nombre.data,
                'tipo': form.tipo.data,
                'pais': form.pais.data,
                'ciudad': form.ciudad.data,
                'descripcion': form.descripcion.data,
                'sitio_web': form.sitio_web.data,
            }
            InstitucionService.actualizar(inst, datos)
            AuditService.registrar('update', 'institucion', inst.id,
                                   datos_anteriores=datos_anteriores, datos_nuevos=datos)
            flash('Institución actualizada.', 'success')
            return redirect(url_for('institucion.detalle', inst_id=inst.id))
        except Exception as e:
            log.error("Error al editar institución", error=str(e))
            db.session.rollback()
            flash('Error al actualizar.', 'error')
    return render_template('instituciones/editar.html', formulario=form, institucion=inst)


@institucion_bp.route('/institucion/<int:inst_id>/miembro/añadir', methods=['POST'])
@login_required
def añadir_miembro(inst_id):
    """Añadir miembro a la institución."""
    inst = Institucion.query.get_or_404(inst_id)
    if not InstitucionService.tiene_permiso(inst, current_user.id, 'invite'):
        abort(403)

    email = request.form.get('email', '').strip().lower()
    rol = request.form.get('rol', 'investigador_externo')

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        flash('Usuario no encontrado con ese email.', 'error')
        return redirect(url_for('institucion.detalle', inst_id=inst_id))

    try:
        InstitucionService.añadir_miembro(inst, usuario.id, rol)
        AuditService.registrar('create', 'usuario_institucion', inst_id,
                               datos_nuevos={'usuario_id': usuario.id, 'rol': rol})
        flash(f'{usuario.nombre_completo} añadido como {rol}.', 'success')
    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('institucion.detalle', inst_id=inst_id))


@institucion_bp.route('/institucion/<int:inst_id>/miembro/<int:usuario_id>/cambiar_rol', methods=['POST'])
@login_required
def cambiar_rol(inst_id, usuario_id):
    """Cambiar el rol de un miembro."""
    inst = Institucion.query.get_or_404(inst_id)
    if not InstitucionService.tiene_permiso(inst, current_user.id, 'manage'):
        abort(403)

    nuevo_rol = request.form.get('rol')
    try:
        InstitucionService.cambiar_rol(inst, usuario_id, nuevo_rol)
        flash('Rol actualizado.', 'success')
    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('institucion.detalle', inst_id=inst_id))


@institucion_bp.route('/institucion/<int:inst_id>/miembro/<int:usuario_id>/remover', methods=['POST'])
@login_required
def remover_miembro(inst_id, usuario_id):
    """Dar de baja a un miembro."""
    inst = Institucion.query.get_or_404(inst_id)
    if not InstitucionService.tiene_permiso(inst, current_user.id, 'manage'):
        abort(403)
    if usuario_id == current_user.id:
        flash('No puedes removerte a ti mismo como director.', 'error')
        return redirect(url_for('institucion.detalle', inst_id=inst_id))

    try:
        InstitucionService.remover_miembro(inst, usuario_id)
        AuditService.registrar('delete', 'usuario_institucion', inst_id,
                               datos_anteriores={'usuario_id': usuario_id})
        flash('Miembro dado de baja.', 'success')
    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('institucion.detalle', inst_id=inst_id))


@institucion_bp.route('/mis-instituciones')
@login_required
def mis_instituciones():
    """Panel del usuario: sus instituciones y roles."""
    instituciones_roles = InstitucionService.get_instituciones_usuario(current_user.id)
    return render_template(
        'instituciones/mis_instituciones.html',
        instituciones_roles=instituciones_roles,
    )


@institucion_bp.route('/api/instituciones/buscar')
@login_required
def api_buscar():
    """API JSON para buscar instituciones (autocompletar)."""
    q = request.args.get('q', '')
    instituciones = InstitucionService.buscar(query=q)
    return jsonify([i.to_dict() for i in instituciones[:10]])
