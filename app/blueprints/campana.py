"""
Blueprint de Campañas - ArqueoTrack v2.0
CRUD de campañas arqueológicas asociadas a yacimientos e instituciones.
"""

import structlog
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.campana import Campana
from app.models.yacimiento import Yacimiento
from app.forms import CampanaForm
from app.services.campana_service import CampanaService
from app.services.audit_service import AuditService

log = structlog.get_logger(__name__)
campana_bp = Blueprint('campana', __name__)


def _get_yacimiento_or_403(yacimiento_id: int) -> Yacimiento:
    """Obtiene el yacimiento y verifica acceso del usuario."""
    yac = Yacimiento.query.get_or_404(yacimiento_id)
    if yac.propietario_id != current_user.id and not yac.tiene_colaborador(current_user):
        abort(403)
    return yac


@campana_bp.route('/yacimientos/<int:yacimiento_id>/campanas')
@login_required
def listar(yacimiento_id: int):
    """Lista campañas de un yacimiento."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    campanas = Campana.query.filter_by(yacimiento_id=yacimiento_id)\
        .order_by(Campana.anio.desc(), Campana.nombre).all()
    return render_template('campanas/listar.html', yacimiento=yac, campanas=campanas)


@campana_bp.route('/yacimientos/<int:yacimiento_id>/campanas/nueva', methods=['GET', 'POST'])
@login_required
def nueva(yacimiento_id: int):
    """Crea una nueva campaña."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    form = CampanaForm()
    if form.validate_on_submit():
        try:
            campana = CampanaService.crear(
                yacimiento_id=yacimiento_id,
                nombre=form.nombre.data,
                anio=form.anio.data,
                codigo=form.codigo.data or None,
                fecha_inicio=form.fecha_inicio.data,
                fecha_fin=form.fecha_fin.data,
                objetivos=form.objetivos.data,
                metodologia=form.metodologia.data,
                presupuesto=form.presupuesto.data,
                financiador=form.financiador.data,
                director_id=current_user.id,
            )
            AuditService.registrar('create', 'campana', campana.id, yacimiento_id=yacimiento_id)
            flash(f'Campaña "{campana.nombre}" creada correctamente.', 'success')
            return redirect(url_for('campana.detalle', yacimiento_id=yacimiento_id, campana_id=campana.id))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('campanas/form.html', form=form, yacimiento=yac, title='Nueva campaña')


@campana_bp.route('/yacimientos/<int:yacimiento_id>/campanas/<int:campana_id>')
@login_required
def detalle(yacimiento_id: int, campana_id: int):
    """Detalle de una campaña."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    campana = Campana.query.filter_by(id=campana_id, yacimiento_id=yacimiento_id).first_or_404()
    stats = CampanaService.estadisticas(campana_id)
    return render_template('campanas/detalle.html', yacimiento=yac, campana=campana, stats=stats)


@campana_bp.route('/yacimientos/<int:yacimiento_id>/campanas/<int:campana_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(yacimiento_id: int, campana_id: int):
    """Edita una campaña."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    campana = Campana.query.filter_by(id=campana_id, yacimiento_id=yacimiento_id).first_or_404()
    form = CampanaForm(obj=campana)
    if form.validate_on_submit():
        try:
            CampanaService.actualizar(campana_id, **{
                k: v for k, v in form.data.items()
                if k not in ('submit', 'csrf_token') and v is not None
            })
            AuditService.registrar('update', 'campana', campana_id, yacimiento_id=yacimiento_id)
            flash('Campaña actualizada.', 'success')
            return redirect(url_for('campana.detalle', yacimiento_id=yacimiento_id, campana_id=campana_id))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('campanas/form.html', form=form, yacimiento=yac, campana=campana, title='Editar campaña')


@campana_bp.route('/yacimientos/<int:yacimiento_id>/campanas/<int:campana_id>/estado', methods=['POST'])
@login_required
def cambiar_estado(yacimiento_id: int, campana_id: int):
    """Cambia el estado de una campaña vía AJAX o form."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    campana = Campana.query.filter_by(id=campana_id, yacimiento_id=yacimiento_id).first_or_404()
    nuevo_estado = request.form.get('estado') or request.json.get('estado', '')
    try:
        CampanaService.cambiar_estado(campana_id, nuevo_estado)
        AuditService.registrar('update', 'campana', campana_id,
                               datos_antes={'estado': campana.estado},
                               datos_despues={'estado': nuevo_estado},
                               yacimiento_id=yacimiento_id)
        if request.is_json:
            return jsonify({'ok': True, 'estado': nuevo_estado})
        flash(f'Estado actualizado a "{nuevo_estado}".', 'success')
    except ValueError as e:
        if request.is_json:
            return jsonify({'ok': False, 'error': str(e)}), 400
        flash(str(e), 'danger')
    return redirect(url_for('campana.detalle', yacimiento_id=yacimiento_id, campana_id=campana_id))


@campana_bp.route('/yacimientos/<int:yacimiento_id>/campanas/<int:campana_id>/eliminar', methods=['POST'])
@login_required
def eliminar(yacimiento_id: int, campana_id: int):
    """Elimina una campaña (solo propietario)."""
    yac = Yacimiento.query.get_or_404(yacimiento_id)
    if yac.propietario_id != current_user.id:
        abort(403)
    campana = Campana.query.filter_by(id=campana_id, yacimiento_id=yacimiento_id).first_or_404()
    nombre = campana.nombre
    db.session.delete(campana)
    db.session.commit()
    AuditService.registrar('delete', 'campana', campana_id, yacimiento_id=yacimiento_id)
    flash(f'Campaña "{nombre}" eliminada.', 'success')
    return redirect(url_for('campana.listar', yacimiento_id=yacimiento_id))
