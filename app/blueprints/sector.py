"""
Blueprint de Sectores - ArqueoTrack 2.0.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user

from app import db
from app.models import Sector, Yacimiento, Hallazgo, Invitacion
from app.forms import SectorForm

sector_bp = Blueprint('sector', __name__)


def _check_sector_write_access(yacimiento, roles=('colaborador', 'asistente')):
    """Verifica acceso de escritura sobre un sector."""
    if yacimiento.user_id == current_user.id:
        return True
    inv = Invitacion.query.filter(
        Invitacion.yacimiento_id == yacimiento.id,
        Invitacion.invitado_id == current_user.id,
        Invitacion.estado == 'aceptada',
        Invitacion.rol.in_(roles),
    ).first()
    return inv is not None


@sector_bp.route('/yacimiento/<int:yacimiento_id>/nuevo_sector', methods=['GET', 'POST'])
@login_required
def nuevo_sector(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    if not _check_sector_write_access(yacimiento):
        abort(403)
    form = SectorForm()
    if form.validate_on_submit():
        try:
            sector = Sector(
                yacimiento_id=yacimiento_id,
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                color=form.color.data,
                lat=form.lat.data,
                lng=form.lng.data,
                polygon_geojson=form.polygon_geojson.data,
                area=form.area.data,
            )
            db.session.add(sector)
            db.session.commit()
            flash('Sector creado.', 'success')
            return redirect(url_for('sector.listar', yacimiento_id=yacimiento_id))
        except Exception:
            db.session.rollback()
            flash('Error al crear el sector.', 'error')
    return render_template('sectores/nuevo.html', formulario=form, yacimiento=yacimiento)


@sector_bp.route('/yacimiento/<int:yacimiento_id>/sectores')
@login_required
def listar(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    puede_ver, _ = current_user.has_permission(yacimiento_id, 'read')
    if not puede_ver:
        abort(403)
    sectores = Sector.query.filter_by(yacimiento_id=yacimiento_id).all()
    sectores_json = [s.to_dict() for s in sectores]
    puede_crear = _check_sector_write_access(yacimiento)
    return render_template(
        'sectores/listar.html',
        yacimiento=yacimiento,
        sectores=sectores,
        sectores_json=sectores_json,
        puede_crear=puede_crear,
        puede_editar_sectores=puede_crear,
        puede_eliminar_sectores=yacimiento.user_id == current_user.id,
        total_hallazgos=sum(s.total_hallazgos for s in sectores),
    )


@sector_bp.route('/yacimiento/<int:yacimiento_id>/mapa_sectores')
@login_required
def mapa_sectores(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    puede_ver, _ = current_user.has_permission(yacimiento_id, 'read')
    if not puede_ver:
        abort(403)
    sectores = Sector.query.filter_by(yacimiento_id=yacimiento_id).all()
    hallazgos = Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).all()
    return render_template(
        'sectores/mapa_sectores.html',
        yacimiento=yacimiento,
        sectores_json=[s.to_dict(include_relations=True) for s in sectores],
        hallazgos_json=[h.to_dict() for h in hallazgos],
    )


@sector_bp.route('/sector/<int:sector_id>')
@login_required
def detalle(sector_id):
    sector = Sector.query.get_or_404(sector_id)
    puede_ver, _ = current_user.has_permission(sector.yacimiento_id, 'read')
    if not puede_ver:
        abort(403)
    return render_template('sectores/detalle.html', sector=sector)


@sector_bp.route('/editar_sector/<int:sector_id>', methods=['GET', 'POST'])
@login_required
def editar(sector_id):
    sector = Sector.query.get_or_404(sector_id)
    puede_editar, _ = current_user.has_permission(sector.yacimiento_id, 'edit')
    if not puede_editar:
        abort(403)
    form = SectorForm(obj=sector)
    if form.validate_on_submit():
        try:
            sector.nombre = form.nombre.data
            sector.descripcion = form.descripcion.data
            sector.color = form.color.data
            sector.lat = form.lat.data
            sector.lng = form.lng.data
            sector.polygon_geojson = form.polygon_geojson.data
            sector.area = form.area.data
            db.session.commit()
            flash('Sector actualizado.', 'success')
            return redirect(url_for('sector.detalle', sector_id=sector.id))
        except Exception:
            db.session.rollback()
            flash('Error al actualizar.', 'error')
    return render_template('sectores/editar.html', formulario=form, sector=sector)


@sector_bp.route('/eliminar_sector/<int:sector_id>', methods=['POST'])
@login_required
def eliminar(sector_id):
    sector = Sector.query.get_or_404(sector_id)
    if sector.yacimiento.user_id != current_user.id:
        abort(403)
    yacimiento_id = sector.yacimiento_id
    db.session.delete(sector)
    db.session.commit()
    flash('Sector eliminado.', 'success')
    return redirect(url_for('sector.listar', yacimiento_id=yacimiento_id))
