"""
Blueprint principal - Dashboard, perfil y búsqueda por código.
ArqueoTrack 2.0.
"""

import structlog
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app import db
from app.models import Hallazgo, Invitacion, Evento, Comentario, Yacimiento
from app.services.yacimiento_service import YacimientoService
from app.services.hallazgo_service import HallazgoService
from app.forms import BuscarCodigoForm
from app.utils.security import is_safe_url

log = structlog.get_logger(__name__)
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def portada():
    """Landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))
    return render_template('portada.html')


@main_bp.route('/inicio')
@login_required
def inicio():
    """Dashboard principal."""
    propios, colaborando = YacimientoService.get_accesibles(current_user.id)
    stats = YacimientoService.estadisticas_globales(current_user.id)
    yacimientos_json = [y.to_dict(include_relations=True) for y in propios]

    return render_template(
        'inicio.html',
        yacimientos=propios,
        yacimientos_colaborando=colaborando,
        yacimientos_json=yacimientos_json,
        **stats,
    )


@main_bp.route('/perfil')
@login_required
def perfil():
    """Perfil del usuario."""
    total_yacimientos = Yacimiento.query.filter_by(user_id=current_user.id).count()
    total_hallazgos = Hallazgo.query.filter_by(user_id=current_user.id).count()
    total_eventos = Evento.query.filter_by(usuario_id=current_user.id).count()
    total_comentarios = Comentario.query.filter_by(usuario_id=current_user.id).count()

    return render_template(
        'perfil.html',
        usuario=current_user,
        total_yacimientos=total_yacimientos,
        total_hallazgos=total_hallazgos,
        total_eventos=total_eventos,
        total_comentarios=total_comentarios,
    )


@main_bp.route('/eliminar_cuenta', methods=['POST'])
@login_required
def eliminar_cuenta():
    """Elimina la cuenta del usuario."""
    from app.services.auth_service import AuthService
    try:
        AuthService.eliminar_cuenta(current_user)
        flash('Tu cuenta ha sido eliminada correctamente.', 'success')
        return redirect(url_for('main.portada'))
    except Exception as e:
        log.error("Error al eliminar cuenta", error=str(e))
        db.session.rollback()
        flash('Error al eliminar la cuenta.', 'error')
        return redirect(url_for('main.perfil'))


@main_bp.route('/buscar_codigo', methods=['GET', 'POST'])
@login_required
def buscar_codigo():
    """Buscar hallazgo por código único."""
    form = BuscarCodigoForm()
    if form.validate_on_submit():
        codigo = form.codigo.data.upper()
        hallazgo = HallazgoService.buscar_por_codigo(codigo)
        if hallazgo:
            puede, _ = current_user.has_permission(hallazgo.yacimiento_id, 'read')
            if hallazgo.user_id == current_user.id or puede:
                return redirect(url_for('hallazgo.detalle', hallazgo_id=hallazgo.id))
            flash('No tienes acceso a este hallazgo.', 'error')
        else:
            flash('Código no encontrado.', 'error')
    return render_template('buscar_codigo.html', formulario=form)


@main_bp.route('/api/buscar-hallazgo', methods=['POST'])
@login_required
def api_buscar_hallazgo():
    """API JSON para buscar hallazgo por código."""
    data = request.get_json()
    if not data or 'codigo' not in data:
        return jsonify({'success': False, 'message': 'Código no proporcionado'}), 400

    hallazgo = HallazgoService.buscar_por_codigo(data['codigo'])
    if not hallazgo:
        return jsonify({'success': False, 'message': 'Código no encontrado'}), 404

    puede, _ = current_user.has_permission(hallazgo.yacimiento_id, 'read')
    if hallazgo.user_id != current_user.id and not puede:
        return jsonify({'success': False, 'message': 'Sin acceso a este hallazgo'}), 403

    return jsonify({
        'success': True,
        'hallazgo': {
            'id': hallazgo.id,
            'codigo': hallazgo.codigo_acceso,
            'tipo': hallazgo.tipo or 'No especificado',
            'descripcion': hallazgo.descripcion or '',
            'yacimiento': hallazgo.yacimiento.nombre if hallazgo.yacimiento else 'No asignado',
            'fecha': hallazgo.fecha.strftime('%d/%m/%Y') if hallazgo.fecha else 'No especificada',
        }
    })
