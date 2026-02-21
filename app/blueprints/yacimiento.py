"""
Blueprint de Yacimientos - ArqueoTrack 2.0.
"""

import structlog
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import Yacimiento, Hallazgo, Sector, FaseProyecto
from app.forms import YacimientoForm, EditarProcesoYacimientoForm
from app.services.yacimiento_service import YacimientoService
from app.utils.time import time_ago

log = structlog.get_logger(__name__)
yacimiento_bp = Blueprint('yacimiento', __name__)


@yacimiento_bp.route('/nuevo_yacimiento', methods=['GET', 'POST'])
@login_required
def nuevo_yacimiento():
    form = YacimientoForm()
    if form.validate_on_submit():
        try:
            datos = {
                'nombre': form.nombre.data,
                'ubicacion': form.ubicacion.data,
                'descripcion': form.descripcion.data,
                'lat': form.lat.data,
                'lng': form.lng.data,
                'polygon_geojson': form.polygon_geojson.data,
                'area_m2': form.area.data,
                'responsable': form.responsable.data,
                'fecha_inicio': form.fecha_inicio.data,
                'fecha_fin': form.fecha_fin.data,
                'altitud_media': form.altitud_media.data,
            }
            yacimiento = YacimientoService.crear(current_user.id, datos)
            flash('Yacimiento creado exitosamente.', 'success')
            return redirect(url_for('yacimiento.detalle', yacimiento_id=yacimiento.id))
        except Exception as e:
            log.error("Error al crear yacimiento", error=str(e))
            db.session.rollback()
            flash('Error al crear el yacimiento.', 'error')
    return render_template('yacimientos/nuevo.html', formulario=form)


@yacimiento_bp.route('/yacimiento/<int:yacimiento_id>')
@login_required
def detalle(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    puede_ver, rol_invitado = current_user.has_permission(yacimiento_id, 'read')
    if not puede_ver:
        abort(403)

    puede_editar, _ = current_user.has_permission(yacimiento_id, 'edit')
    puede_crear, _ = current_user.has_permission(yacimiento_id, 'create')
    es_propietario = yacimiento.user_id == current_user.id
    rol_usuario = 'propietario' if es_propietario else rol_invitado

    hallazgos = Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).all()
    sectores = Sector.query.filter_by(yacimiento_id=yacimiento_id).all()
    fases = FaseProyecto.query.filter_by(yacimiento_id=yacimiento_id).all()

    return render_template(
        'yacimientos/detalle.html',
        yacimiento=yacimiento,
        hallazgos=hallazgos,
        sectores=sectores,
        fases=fases,
        puede_editar=puede_editar,
        puede_crear=puede_crear,
        es_propietario=es_propietario,
        rol_usuario=rol_usuario,
        total_hallazgos=len(hallazgos),
        total_sectores=len(sectores),
        total_fases=len(fases),
        hallazgos_con_foto=sum(1 for h in hallazgos if h.foto),
    )


@yacimiento_bp.route('/editar_yacimiento/<int:yacimiento_id>', methods=['GET', 'POST'])
@login_required
def editar(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    if yacimiento.user_id != current_user.id:
        abort(403)

    form = YacimientoForm(obj=yacimiento)
    if form.validate_on_submit():
        try:
            datos = {
                'nombre': form.nombre.data,
                'ubicacion': form.ubicacion.data,
                'descripcion': form.descripcion.data,
                'lat': form.lat.data,
                'lng': form.lng.data,
                'polygon_geojson': form.polygon_geojson.data,
                'area_m2': form.area.data,
                'responsable': form.responsable.data,
                'fecha_inicio': form.fecha_inicio.data,
                'fecha_fin': form.fecha_fin.data,
                'altitud_media': form.altitud_media.data,
            }
            YacimientoService.actualizar(yacimiento, datos)
            flash('Yacimiento actualizado.', 'success')
            return redirect(url_for('yacimiento.detalle', yacimiento_id=yacimiento.id))
        except Exception as e:
            log.error("Error al editar yacimiento", error=str(e))
            db.session.rollback()
            flash('Error al actualizar.', 'error')
    return render_template('yacimientos/editar.html', formulario=form, yacimiento=yacimiento)


@yacimiento_bp.route('/eliminar_yacimiento/<int:yacimiento_id>', methods=['POST'])
@login_required
def eliminar(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    if yacimiento.user_id != current_user.id:
        abort(403)
    YacimientoService.eliminar(yacimiento)
    flash('Yacimiento eliminado.', 'success')
    return redirect(url_for('main.inicio'))
