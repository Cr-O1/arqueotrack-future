"""
Application Factory de ArqueoTrack 2.0
"""

import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_caching import Cache

# ── Extensiones (sin app binding aún) ────────────────────────────────────────
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
migrate = Migrate()
cache = Cache()


def create_app(config_name: str = None) -> Flask:
    """
    Crea y configura la aplicación Flask.

    Args:
        config_name: Nombre del entorno ('development', 'testing', 'production').
                     Si no se indica, usa la variable FLASK_ENV.

    Returns:
        Instancia de Flask configurada.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static'),
    )

    # ── Configuración ─────────────────────────────────────────────────────────
    from config import get_config
    app.config.from_object(get_config(config_name))

    # ── Logging estructurado ──────────────────────────────────────────────────
    from app.logging_config import setup_logging
    setup_logging(app)

    # ── Directorio de uploads ─────────────────────────────────────────────────
    upload_path = os.path.join(project_root, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_path, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_path

    # ── Inicializar extensiones ───────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    # ── Login manager ─────────────────────────────────────────────────────────
    login_manager.login_view = 'auth.iniciar_sesion'
    login_manager.login_message_category = 'info'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

    from app.models.user import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    # ── Blueprints ────────────────────────────────────────────────────────────
    _register_blueprints(app)

    # ── Rutas de utilidad ─────────────────────────────────────────────────────
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # ── Manejadores de error ──────────────────────────────────────────────────
    _register_error_handlers(app)

    # ── Crear tablas en entornos sin migraciones (testing/SQLite dev) ─────────
    if app.config.get('TESTING'):
        with app.app_context():
            db.create_all()

    return app


def _register_blueprints(app: Flask) -> None:
    """Registra todos los blueprints de la aplicación."""
    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.yacimiento import yacimiento_bp
    from app.blueprints.hallazgo import hallazgo_bp
    from app.blueprints.sector import sector_bp
    from app.blueprints.fase import fase_bp
    from app.blueprints.evento import evento_bp
    from app.blueprints.invitacion import invitacion_bp
    # v2.0 — Institucionalización
    from app.blueprints.institucion import institucion_bp
    from app.blueprints.campana import campana_bp
    # v3.0 — Arqueología Científica
    from app.blueprints.ue import ue_bp
    from app.blueprints.muestra import muestra_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(yacimiento_bp)
    app.register_blueprint(hallazgo_bp)
    app.register_blueprint(sector_bp)
    app.register_blueprint(fase_bp)
    app.register_blueprint(evento_bp)
    app.register_blueprint(invitacion_bp)
    app.register_blueprint(institucion_bp)
    app.register_blueprint(campana_bp)
    app.register_blueprint(ue_bp)
    app.register_blueprint(muestra_bp)


def _register_error_handlers(app: Flask) -> None:
    """Registra los manejadores de error HTTP."""
    from flask import render_template

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errores/404.html'), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errores/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errores/500.html'), 500
