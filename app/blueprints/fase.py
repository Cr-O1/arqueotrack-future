"""
Blueprint de Fases de Proyecto - ArqueoTrack 2.0.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import FaseProyecto, Yacimiento, Evento
from app.forms import FaseForm

fase_bp = Blueprint('fase', __name__)


@fase_bp.route('/yacimiento/<int:yacimiento_id>/fases/nueva', methods=['GET', 'POST'])
@login_required
def nueva(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    puede_crear, _ = current_user.has_permission(yacimiento_id, 'create')
    if not puede_crear:
        abort(403)

    form = FaseForm()
    if form.validate_on_submit():
        try:
            fase = FaseProyecto(
                yacimiento_id=yacimiento_id,
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                estado=form.estado.data,
                fecha_inicio=form.fecha_inicio.data,
                fecha_fin=form.fecha_fin.data,
                objetivos=form.objetivos.data,
                metodologia=form.metodologia.data,
                recursos_necesarios=form.recursos_necesarios.data,
                resultados_esperados=form.resultados_esperados.data,
                presupuesto=form.presupuesto.data,
                equipo_participante=form.equipo_participante.data,
                notas=form.notas.data,
            )
            db.session.add(fase)
            db.session.commit()
            flash('Fase creada.', 'success')
            return redirect(url_for('fase.listar', yacimiento_id=yacimiento_id))
        except Exception:
            db.session.rollback()
            flash('Error al crear la fase.', 'error')
    return render_template('fases/nueva.html', formulario=form, yacimiento=yacimiento)


@fase_bp.route('/yacimiento/<int:yacimiento_id>/fases')
@login_required
def listar(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    puede_ver, _ = current_user.has_permission(yacimiento_id, 'read')
    if not puede_ver:
        abort(403)
    fases = FaseProyecto.query.filter_by(yacimiento_id=yacimiento_id).order_by(FaseProyecto.orden).all()
    puede_crear, _ = current_user.has_permission(yacimiento_id, 'create')
    return render_template('fases/listar.html', yacimiento=yacimiento, fases=fases, puede_crear=puede_crear)


@fase_bp.route('/fase/<int:fase_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(fase_id):
    fase = FaseProyecto.query.get_or_404(fase_id)
    puede_editar, _ = current_user.has_permission(fase.yacimiento_id, 'edit')
    if not puede_editar:
        abort(403)
    form = FaseForm(obj=fase)
    if form.validate_on_submit():
        try:
            fase.nombre = form.nombre.data
            fase.descripcion = form.descripcion.data
            fase.estado = form.estado.data
            fase.fecha_inicio = form.fecha_inicio.data
            fase.fecha_fin = form.fecha_fin.data
            fase.objetivos = form.objetivos.data
            fase.metodologia = form.metodologia.data
            fase.recursos_necesarios = form.recursos_necesarios.data
            fase.resultados_esperados = form.resultados_esperados.data
            fase.presupuesto = form.presupuesto.data
            fase.equipo_participante = form.equipo_participante.data
            fase.notas = form.notas.data
            db.session.commit()
            flash('Fase actualizada.', 'success')
            return redirect(url_for('fase.listar', yacimiento_id=fase.yacimiento_id))
        except Exception:
            db.session.rollback()
            flash('Error al actualizar.', 'error')
    return render_template('fases/editar.html', formulario=form, fase=fase)


@fase_bp.route('/fase/<int:fase_id>/eliminar', methods=['POST'])
@login_required
def eliminar(fase_id):
    fase = FaseProyecto.query.get_or_404(fase_id)
    puede_eliminar, _ = current_user.has_permission(fase.yacimiento_id, 'delete')
    if not puede_eliminar:
        abort(403)
    yacimiento_id = fase.yacimiento_id
    db.session.delete(fase)
    db.session.commit()
    flash('Fase eliminada.', 'success')
    return redirect(url_for('fase.listar', yacimiento_id=yacimiento_id))
