"""
Blueprint de autenticación - ArqueoTrack 2.0.
Delega la lógica de negocio a AuthService.
"""

import structlog
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.services.auth_service import AuthService
from app.forms import RegistroForm, LoginForm
from app.utils.security import is_safe_url

log = structlog.get_logger(__name__)
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    """Registro de nuevos usuarios."""
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))

    form = RegistroForm()
    if form.validate_on_submit():
        try:
            AuthService.registrar({
                'nombre_usuario': form.nombre_usuario.data,
                'nombre': form.nombre.data,
                'apellidos': form.apellidos.data,
                'email': form.correo_electronico.data,
                'fecha_nacimiento': form.fecha_nacimiento.data,
                'ocupacion': form.ocupacion.data,
                'contraseña': form.contraseña.data,
            })
            flash('¡Cuenta creada exitosamente! Por favor inicia sesión.', 'success')
            return redirect(url_for('auth.iniciar_sesion'))
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            log.error("Error en registro", error=str(e))
            flash('Error al registrar la cuenta. Inténtalo de nuevo.', 'error')

    return render_template('registro.html', formulario=form)


@auth_bp.route('/iniciar-sesion', methods=['GET', 'POST'])
def iniciar_sesion():
    """Inicio de sesión."""
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = AuthService.autenticar(
            email=form.correo_electronico.data,
            contraseña=form.contraseña.data,
        )
        if usuario:
            login_user(usuario)
            log.info("Usuario autenticado", user_id=usuario.id)
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('main.inicio'))
        flash('Credenciales inválidas.', 'error')

    return render_template('iniciar_sesion.html', formulario=form)


@auth_bp.route('/cerrar-sesion')
@login_required
def cerrar_sesion():
    """Cierre de sesión."""
    log.info("Usuario cerró sesión", user_id=current_user.id)
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('main.portada'))
