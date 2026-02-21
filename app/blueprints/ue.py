"""
Blueprint de Unidades Estratigráficas - ArqueoTrack v3.0
CRUD de UEs y gestión de la Matriz de Harris.
"""

import structlog
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.unidad_estratigrafica import UnidadEstratigrafica, RelacionUE
from app.models.yacimiento import Yacimiento
from app.forms import UnidadEstratigraficaForm, RelacionUEForm
from app.services.ue_service import UEService
from app.services.harris_service import HarrisService
from app.services.audit_service import AuditService

log = structlog.get_logger(__name__)
ue_bp = Blueprint('ue', __name__)


def _get_yacimiento_or_403(yacimiento_id: int) -> Yacimiento:
    yac = Yacimiento.query.get_or_404(yacimiento_id)
    if yac.propietario_id != current_user.id and not yac.tiene_colaborador(current_user):
        abort(403)
    return yac


@ue_bp.route('/yacimientos/<int:yacimiento_id>/ues')
@login_required
def listar(yacimiento_id: int):
    """Lista todas las UEs del yacimiento."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    ues = UnidadEstratigrafica.query.filter_by(yacimiento_id=yacimiento_id)\
        .order_by(UnidadEstratigrafica.numero_ue).all()
    return render_template('ues/listar.html', yacimiento=yac, ues=ues)


@ue_bp.route('/yacimientos/<int:yacimiento_id>/ues/nueva', methods=['GET', 'POST'])
@login_required
def nueva(yacimiento_id: int):
    """Crea una nueva UE."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    from app.models.campana import Campana
    from app.models.sector import Sector
    form = UnidadEstratigraficaForm()
    form.campana_id.choices = [(0, '— Sin campaña —')] + [
        (c.id, f'{c.anio} · {c.nombre}')
        for c in Campana.query.filter_by(yacimiento_id=yacimiento_id).order_by(Campana.anio.desc()).all()
    ]
    form.sector_id.choices = [(0, '— Sin sector —')] + [
        (s.id, s.nombre)
        for s in Sector.query.filter_by(yacimiento_id=yacimiento_id).all()
    ]
    if form.validate_on_submit():
        try:
            ue = UEService.crear(
                yacimiento_id=yacimiento_id,
                tipo=form.tipo.data,
                descripcion=form.descripcion.data,
                interpretacion=form.interpretacion.data,
                color_munsell=form.color_munsell.data or None,
                textura=form.textura.data or None,
                compactacion=form.compactacion.data or None,
                composicion=form.composicion.data,
                cota_superior=form.cota_superior.data,
                cota_inferior=form.cota_inferior.data,
                area_m2=form.area_m2.data,
                campana_id=form.campana_id.data or None,
                sector_id=form.sector_id.data or None,
                registrada_por_id=current_user.id,
                numero_ue=form.numero_ue.data,
            )
            AuditService.registrar('create', 'unidad_estratigrafica', ue.id, yacimiento_id=yacimiento_id)
            flash(f'UE {ue.numero_ue} creada correctamente.', 'success')
            return redirect(url_for('ue.detalle', yacimiento_id=yacimiento_id, ue_id=ue.id))
        except ValueError as e:
            flash(str(e), 'danger')
    siguiente = UEService.siguiente_numero(yacimiento_id)
    return render_template('ues/form.html', form=form, yacimiento=yac, siguiente=siguiente, title='Nueva UE')


@ue_bp.route('/yacimientos/<int:yacimiento_id>/ues/<int:ue_id>')
@login_required
def detalle(yacimiento_id: int, ue_id: int):
    """Detalle de una UE con sus relaciones."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    ue = UnidadEstratigrafica.query.filter_by(id=ue_id, yacimiento_id=yacimiento_id).first_or_404()
    form_relacion = RelacionUEForm()
    otras_ues = UnidadEstratigrafica.query.filter(
        UnidadEstratigrafica.yacimiento_id == yacimiento_id,
        UnidadEstratigrafica.id != ue_id,
    ).order_by(UnidadEstratigrafica.numero_ue).all()
    form_relacion.ue_anterior_id.choices = [(u.id, f'UE {u.numero_ue}') for u in otras_ues]
    return render_template('ues/detalle.html', yacimiento=yac, ue=ue, form_relacion=form_relacion)


@ue_bp.route('/yacimientos/<int:yacimiento_id>/ues/<int:ue_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(yacimiento_id: int, ue_id: int):
    """Edita una UE."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    from app.models.campana import Campana
    from app.models.sector import Sector
    ue = UnidadEstratigrafica.query.filter_by(id=ue_id, yacimiento_id=yacimiento_id).first_or_404()
    form = UnidadEstratigraficaForm(obj=ue)
    form.campana_id.choices = [(0, '— Sin campaña —')] + [
        (c.id, f'{c.anio} · {c.nombre}')
        for c in Campana.query.filter_by(yacimiento_id=yacimiento_id).order_by(Campana.anio.desc()).all()
    ]
    form.sector_id.choices = [(0, '— Sin sector —')] + [
        (s.id, s.nombre) for s in Sector.query.filter_by(yacimiento_id=yacimiento_id).all()
    ]
    if form.validate_on_submit():
        try:
            UEService.actualizar(ue_id, **{
                k: v for k, v in form.data.items()
                if k not in ('submit', 'csrf_token')
            })
            AuditService.registrar('update', 'unidad_estratigrafica', ue_id, yacimiento_id=yacimiento_id)
            flash('UE actualizada.', 'success')
            return redirect(url_for('ue.detalle', yacimiento_id=yacimiento_id, ue_id=ue_id))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('ues/form.html', form=form, yacimiento=yac, ue=ue, title=f'Editar UE {ue.numero_ue}')


@ue_bp.route('/yacimientos/<int:yacimiento_id>/ues/<int:ue_id>/relacion', methods=['POST'])
@login_required
def añadir_relacion(yacimiento_id: int, ue_id: int):
    """Añade una relación Harris entre esta UE (posterior) y otra (anterior)."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    ue = UnidadEstratigrafica.query.filter_by(id=ue_id, yacimiento_id=yacimiento_id).first_or_404()
    otras_ues = UnidadEstratigrafica.query.filter(
        UnidadEstratigrafica.yacimiento_id == yacimiento_id,
        UnidadEstratigrafica.id != ue_id,
    ).order_by(UnidadEstratigrafica.numero_ue).all()
    form_relacion = RelacionUEForm()
    form_relacion.ue_anterior_id.choices = [(u.id, f'UE {u.numero_ue}') for u in otras_ues]
    if form_relacion.validate_on_submit():
        try:
            HarrisService.añadir_relacion(
                ue_posterior_id=ue_id,
                ue_anterior_id=form_relacion.ue_anterior_id.data,
                tipo_relacion=form_relacion.tipo_relacion.data,
                notas=form_relacion.notas.data,
                confirmada=form_relacion.confirmada.data,
            )
            flash('Relación añadida a la Matriz de Harris.', 'success')
        except ValueError as e:
            flash(str(e), 'danger')
    return redirect(url_for('ue.detalle', yacimiento_id=yacimiento_id, ue_id=ue_id))


@ue_bp.route('/yacimientos/<int:yacimiento_id>/ues/<int:ue_id>/relacion/<int:relacion_id>/eliminar', methods=['POST'])
@login_required
def eliminar_relacion(yacimiento_id: int, ue_id: int, relacion_id: int):
    """Elimina una relación Harris."""
    _get_yacimiento_or_403(yacimiento_id)
    HarrisService.eliminar_relacion(relacion_id)
    flash('Relación eliminada.', 'success')
    return redirect(url_for('ue.detalle', yacimiento_id=yacimiento_id, ue_id=ue_id))


@ue_bp.route('/yacimientos/<int:yacimiento_id>/harris')
@login_required
def harris(yacimiento_id: int):
    """Vista de la Matriz de Harris completa del yacimiento."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    return render_template('ues/harris.html', yacimiento=yac)


@ue_bp.route('/yacimientos/<int:yacimiento_id>/harris/json')
@login_required
def harris_json(yacimiento_id: int):
    """API JSON para D3.js — nodos y aristas de la Matriz de Harris."""
    _get_yacimiento_or_403(yacimiento_id)
    data = UEService.get_harris_json(yacimiento_id)
    return jsonify(data)


@ue_bp.route('/yacimientos/<int:yacimiento_id>/harris/export.<fmt>')
@login_required
def harris_export(yacimiento_id: int, fmt: str):
    """Exporta la Matriz de Harris en GraphML o JSON."""
    _get_yacimiento_or_403(yacimiento_id)
    if fmt == 'graphml':
        content = HarrisService.exportar_graphml(yacimiento_id)
        from flask import Response
        return Response(content, mimetype='application/xml',
                        headers={'Content-Disposition': f'attachment; filename=harris_{yacimiento_id}.graphml'})
    elif fmt == 'json':
        return jsonify(HarrisService.exportar_json(yacimiento_id))
    abort(404)


@ue_bp.route('/yacimientos/<int:yacimiento_id>/ues/<int:ue_id>/eliminar', methods=['POST'])
@login_required
def eliminar(yacimiento_id: int, ue_id: int):
    """Elimina una UE."""
    yac = Yacimiento.query.get_or_404(yacimiento_id)
    if yac.propietario_id != current_user.id:
        abort(403)
    ue = UnidadEstratigrafica.query.filter_by(id=ue_id, yacimiento_id=yacimiento_id).first_or_404()
    numero = ue.numero_ue
    UEService.eliminar(ue_id)
    AuditService.registrar('delete', 'unidad_estratigrafica', ue_id, yacimiento_id=yacimiento_id)
    flash(f'UE {numero} eliminada.', 'success')
    return redirect(url_for('ue.listar', yacimiento_id=yacimiento_id))
