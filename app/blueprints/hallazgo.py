"""
Blueprint de Hallazgos - ArqueoTrack 2.0.
"""

import structlog
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user

from app import db
from app.models import Hallazgo, Yacimiento, Sector, Comentario
from app.forms import HallazgoForm
from app.services.hallazgo_service import HallazgoService
from app.utils.time import time_ago

log = structlog.get_logger(__name__)
hallazgo_bp = Blueprint('hallazgo', __name__)


@hallazgo_bp.route('/nuevo_hallazgo/<int:yacimiento_id>', methods=['GET', 'POST'])
@login_required
def nuevo(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    puede_crear, _ = current_user.has_permission(yacimiento_id, 'create')
    if not puede_crear:
        abort(403)

    form = HallazgoForm()
    form.sector_id.choices = [(0, 'Sin sector')] + [
        (s.id, s.nombre) for s in Sector.query.filter_by(yacimiento_id=yacimiento_id).all()
    ]

    if form.validate_on_submit():
        try:
            datos = {
                'sector_id': form.sector_id.data if form.sector_id.data != 0 else None,
                'tipo': form.tipo.data,
                'material': form.material.data,
                'datacion': form.datacion.data,
                'dimensiones': form.dimensiones.data,
                'peso': form.peso.data,
                'estado_conservacion': form.estado_conservacion.data,
                'descripcion': form.descripcion.data,
                'ubicacion': form.ubicacion.data,
                'lat': form.lat.data,
                'lng': form.lng.data,
                'altitud': form.altitud.data,
                'fecha': form.fecha.data,
                'proceso_extraccion': form.proceso_extraccion.data,
                'destino': form.destino.data,
                'notas': form.notas.data,
            }
            foto = request.files.get('foto')
            hallazgo = HallazgoService.crear(
                user_id=current_user.id,
                yacimiento_id=yacimiento_id,
                datos=datos,
                foto=foto,
                upload_folder=current_app.config['UPLOAD_FOLDER'],
            )
            flash('Hallazgo registrado.', 'success')
            return redirect(url_for('hallazgo.detalle', hallazgo_id=hallazgo.id))
        except Exception as e:
            log.error("Error al crear hallazgo", error=str(e))
            db.session.rollback()
            flash('Error al registrar el hallazgo.', 'error')

    return render_template('hallazgos/nuevo.html', formulario=form, yacimiento=yacimiento)


@hallazgo_bp.route('/hallazgo/<int:hallazgo_id>')
@login_required
def detalle(hallazgo_id):
    hallazgo = Hallazgo.query.get_or_404(hallazgo_id)
    puede_ver, rol = current_user.has_permission(hallazgo.yacimiento_id, 'read')
    if hallazgo.user_id != current_user.id and not puede_ver:
        abort(403)

    puede_editar, _ = current_user.has_permission(hallazgo.yacimiento_id, 'edit')
    comentarios = hallazgo.comentarios.all()

    return render_template(
        'hallazgos/detalle.html',
        hallazgo=hallazgo,
        comentarios=comentarios,
        puede_editar=puede_editar,
        time_ago=time_ago,
    )


@hallazgo_bp.route('/editar_hallazgo/<int:hallazgo_id>', methods=['GET', 'POST'])
@login_required
def editar(hallazgo_id):
    hallazgo = Hallazgo.query.get_or_404(hallazgo_id)
    puede_editar, _ = current_user.has_permission(hallazgo.yacimiento_id, 'edit')
    if not puede_editar:
        abort(403)

    form = HallazgoForm(obj=hallazgo)
    form.sector_id.choices = [(0, 'Sin sector')] + [
        (s.id, s.nombre) for s in Sector.query.filter_by(yacimiento_id=hallazgo.yacimiento_id).all()
    ]

    if form.validate_on_submit():
        try:
            datos = {
                'sector_id': form.sector_id.data if form.sector_id.data != 0 else None,
                'tipo': form.tipo.data,
                'material': form.material.data,
                'datacion': form.datacion.data,
                'dimensiones': form.dimensiones.data,
                'peso': form.peso.data,
                'estado_conservacion': form.estado_conservacion.data,
                'descripcion': form.descripcion.data,
                'ubicacion': form.ubicacion.data,
                'lat': form.lat.data,
                'lng': form.lng.data,
                'altitud': form.altitud.data,
                'fecha': form.fecha.data,
                'proceso_extraccion': form.proceso_extraccion.data,
                'destino': form.destino.data,
                'notas': form.notas.data,
            }
            HallazgoService.actualizar(hallazgo, datos)
            flash('Hallazgo actualizado.', 'success')
            return redirect(url_for('hallazgo.detalle', hallazgo_id=hallazgo.id))
        except Exception as e:
            log.error("Error al editar hallazgo", error=str(e))
            db.session.rollback()
            flash('Error al actualizar.', 'error')

    return render_template('hallazgos/editar.html', formulario=form, hallazgo=hallazgo)


@hallazgo_bp.route('/eliminar_hallazgo/<int:hallazgo_id>', methods=['POST'])
@login_required
def eliminar(hallazgo_id):
    hallazgo = Hallazgo.query.get_or_404(hallazgo_id)
    puede_eliminar, _ = current_user.has_permission(hallazgo.yacimiento_id, 'delete')
    if not puede_eliminar:
        abort(403)
    yacimiento_id = hallazgo.yacimiento_id
    HallazgoService.eliminar(hallazgo)
    flash('Hallazgo eliminado.', 'success')
    return redirect(url_for('yacimiento.detalle', yacimiento_id=yacimiento_id))


@hallazgo_bp.route('/hallazgo/<int:hallazgo_id>/comentar', methods=['POST'])
@login_required
def comentar(hallazgo_id):
    hallazgo = Hallazgo.query.get_or_404(hallazgo_id)
    puede_ver, _ = current_user.has_permission(hallazgo.yacimiento_id, 'read')
    if hallazgo.user_id != current_user.id and not puede_ver:
        abort(403)

    contenido = request.form.get('contenido', '').strip()
    if contenido:
        comentario = Comentario(
            hallazgo_id=hallazgo_id,
            usuario_id=current_user.id,
            contenido=contenido,
        )
        db.session.add(comentario)
        db.session.commit()
        flash('Comentario añadido.', 'success')

    return redirect(url_for('hallazgo.detalle', hallazgo_id=hallazgo_id))
