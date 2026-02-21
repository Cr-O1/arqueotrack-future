"""
Punto de entrada de ArqueoTrack 2.0.
Soporta desarrollo local, Replit y Docker.
"""

import os
import click
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db

app = create_app()


# ── Auto-setup para Replit ────────────────────────────────────────────────────
def setup_replit():
    """Configuración automática para entorno Replit."""
    with app.app_context():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        db.create_all()
        app.logger.info("Replit: base de datos inicializada.")


# ── Comandos CLI ──────────────────────────────────────────────────────────────
@app.cli.command('init-db')
def init_db():
    """Inicializa las tablas de la base de datos (sin Alembic)."""
    with app.app_context():
        db.create_all()
        click.echo('✅ Base de datos inicializada.')


@app.cli.command('seed-db')
def seed_db():
    """Carga datos de ejemplo para desarrollo."""
    with app.app_context():
        from app.models.user import Usuario
        from app.models.yacimiento import Yacimiento

        if Usuario.query.filter_by(email='demo@arqueotrack.com').first():
            click.echo('ℹ️  Los datos de ejemplo ya existen.')
            return

        usuario = Usuario(
            nombre_usuario='demo',
            nombre='Usuario',
            apellidos='Demo',
            email='demo@arqueotrack.com',
            fecha_nacimiento='1990-01-01',
            ocupacion='arqueologo',
        )
        usuario.set_password('demo12345678')
        db.session.add(usuario)
        db.session.flush()

        yacimiento = Yacimiento(
            user_id=usuario.id,
            nombre='Yacimiento Demo',
            ubicacion='Madrid, España',
            descripcion='Yacimiento de demostración con datos de ejemplo.',
            lat=40.416775,
            lng=-3.703790,
        )
        db.session.add(yacimiento)
        db.session.commit()

        click.echo('✅ Datos de ejemplo cargados.')
        click.echo('   Usuario: demo@arqueotrack.com')
        click.echo('   Contraseña: demo12345678')


@app.cli.command('test')
@click.option('--coverage', is_flag=True, help='Ejecutar con cobertura de código.')
def run_tests(coverage):
    """Ejecuta la suite de tests."""
    import subprocess
    cmd = ['python', '-m', 'pytest']
    if coverage:
        cmd += ['--cov=app', '--cov-report=term-missing', '--cov-report=html']
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)


# ── Arranque ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Auto-setup en Replit
    if os.getenv('REPL_ID'):
        print('🏺 Configurando ArqueoTrack en Replit...')
        setup_replit()

    port = int(os.getenv('PORT', 5000))

    print('=' * 50)
    print('🏺 ArqueoTrack 2.0')
    print(f'   Entorno : {os.getenv("FLASK_ENV", "development")}')
    print(f'   Puerto  : {port}')
    print('=' * 50)

    app.run(host='0.0.0.0', port=port, debug=app.debug)
