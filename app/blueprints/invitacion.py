"""
Blueprint de Invitaciones - ArqueoTrack 2.0.
"""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.models import Invitacion, Yacimiento, Usuario
from app.forms import InvitacionForm

invitacion_bp = Blueprint('invitacion', __name__)


@invitacion_bp.route('/yacimiento/<int:yacimiento_id>/invitar', methods=['GET', 'POST'])
@login_required
def invitar(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    if yacimiento.user_id != current_user.id:
        abort(403)

    form = InvitacionForm()
    if form.validate_on_submit():
        email = (form.email.data or '').strip().lower()
        usuario = Usuario.query.filter(func.lower(Usuario.email) == email).first()
        if not usuario:
            flash('Usuario no encontrado.', 'error')
        elif Invitacion.query.filter_by(yacimiento_id=yacimiento_id, invitado_id=usuario.id, estado='pendiente').first():
            flash('Ya existe una invitación pendiente para este usuario.', 'error')
        else:
            try:
                invitacion = Invitacion(
                    yacimiento_id=yacimiento_id,
                    invitado_id=usuario.id,
                    invitado_por_id=current_user.id,
                    email=email,
                    rol=form.rol.data,
                    mensaje=form.mensaje.data,
                )
                db.session.add(invitacion)
                db.session.commit()
                flash('Invitación enviada.', 'success')
                return redirect(url_for('invitacion.gestionar', yacimiento_id=yacimiento_id))
            except Exception:
                db.session.rollback()
                flash('Error al enviar la invitación.', 'error')
    return render_template('invitaciones/nueva.html', formulario=form, yacimiento=yacimiento)


@invitacion_bp.route('/yacimiento/<int:yacimiento_id>/invitaciones')
@login_required
def gestionar(yacimiento_id):
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    if yacimiento.user_id != current_user.id:
        abort(403)
    invitaciones = Invitacion.query.filter_by(yacimiento_id=yacimiento_id).all()
    return render_template('invitaciones/gestionar.html', yacimiento=yacimiento, invitaciones=invitaciones)


@invitacion_bp.route('/invitaciones/pendientes')
@login_required
def pendientes():
    invitaciones = Invitacion.query.filter_by(invitado_id=current_user.id, estado='pendiente').all()
    return render_template('invitaciones/pendientes.html', invitaciones=invitaciones)


@invitacion_bp.route('/invitacion/<int:invitacion_id>/aceptar', methods=['POST'])
@login_required
def aceptar(invitacion_id):
    invitacion = Invitacion.query.get_or_404(invitacion_id)
    if invitacion.invitado_id != current_user.id:
        abort(403)
    invitacion.estado = 'aceptada'
    invitacion.fecha_respuesta = datetime.utcnow()
    db.session.commit()
    flash(f'Has aceptado la invitación a {invitacion.yacimiento.nombre}.', 'success')
    return redirect(url_for('invitacion.pendientes'))


@invitacion_bp.route('/invitacion/<int:invitacion_id>/rechazar', methods=['POST'])
@login_required
def rechazar(invitacion_id):
    invitacion = Invitacion.query.get_or_404(invitacion_id)
    if invitacion.invitado_id != current_user.id:
        abort(403)
    invitacion.estado = 'rechazada'
    invitacion.fecha_respuesta = datetime.utcnow()
    db.session.commit()
    flash('Invitación rechazada.', 'info')
    return redirect(url_for('invitacion.pendientes'))


@invitacion_bp.route('/invitacion/<int:invitacion_id>/revocar', methods=['POST'])
@login_required
def revocar(invitacion_id):
    invitacion = Invitacion.query.get_or_404(invitacion_id)
    if invitacion.yacimiento.user_id != current_user.id:
        abort(403)
    db.session.delete(invitacion)
    db.session.commit()
    flash('Invitación revocada.', 'success')
    return redirect(url_for('invitacion.gestionar', yacimiento_id=invitacion.yacimiento_id))
