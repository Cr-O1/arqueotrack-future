"""
Blueprint de Eventos (Timeline) - ArqueoTrack 2.0.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import Evento, Yacimiento, FaseProyecto, Hallazgo, Sector
from app.forms import EventoForm
from app.utils.time import time_ago

evento_bp = Blueprint('evento', __name__)


@evento_bp.route('/yacimiento/<int:yacimiento_id>/eventos')
@login_required
def listar(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    puede_ver, _ = current_user.has_permission(yacimiento_id, 'read')
    if not puede_ver:
        abort(403)
    eventos = Evento.query.filter_by(yacimiento_id=yacimiento_id).order_by(Evento.fecha.desc()).all()
    puede_crear, _ = current_user.has_permission(yacimiento_id, 'create')
    return render_template('eventos/listar.html', yacimiento=yacimiento, eventos=eventos, puede_crear=puede_crear, time_ago=time_ago)


@evento_bp.route('/yacimiento/<int:yacimiento_id>/eventos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    puede_crear, _ = current_user.has_permission(yacimiento_id, 'create')
    if not puede_crear:
        abort(403)

    form = EventoForm()
    form.fase_id.choices = [(0, 'Sin fase')] + [(f.id, f.nombre) for f in FaseProyecto.query.filter_by(yacimiento_id=yacimiento_id).all()]
    form.hallazgo_id.choices = [(0, 'Sin hallazgo')] + [(h.id, h.codigo_acceso) for h in Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).all()]
    form.sector_id.choices = [(0, 'Sin sector')] + [(s.id, s.nombre) for s in Sector.query.filter_by(yacimiento_id=yacimiento_id).all()]

    if form.validate_on_submit():
        try:
            evento = Evento(
                yacimiento_id=yacimiento_id,
                usuario_id=current_user.id,
                tipo=form.tipo.data,
                titulo=form.titulo.data,
                descripcion=form.descripcion.data,
                fecha=form.fecha.data,
                prioridad=form.prioridad.data,
                estado_evento=form.estado_evento.data,
                participantes=form.participantes.data,
                resultados=form.resultados.data,
                fase_id=form.fase_id.data if form.fase_id.data != 0 else None,
                hallazgo_id=form.hallazgo_id.data if form.hallazgo_id.data != 0 else None,
                sector_id=form.sector_id.data if form.sector_id.data != 0 else None,
            )
            db.session.add(evento)
            db.session.commit()
            flash('Evento registrado.', 'success')
            return redirect(url_for('evento.listar', yacimiento_id=yacimiento_id))
        except Exception:
            db.session.rollback()
            flash('Error al crear el evento.', 'error')
    return render_template('eventos/nuevo.html', formulario=form, yacimiento=yacimiento)


@evento_bp.route('/evento/<int:evento_id>/eliminar', methods=['POST'])
@login_required
def eliminar(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    puede_eliminar, _ = current_user.has_permission(evento.yacimiento_id, 'delete')
    if not puede_eliminar:
        abort(403)
    yacimiento_id = evento.yacimiento_id
    db.session.delete(evento)
    db.session.commit()
    flash('Evento eliminado.', 'success')
    return redirect(url_for('evento.listar', yacimiento_id=yacimiento_id))
