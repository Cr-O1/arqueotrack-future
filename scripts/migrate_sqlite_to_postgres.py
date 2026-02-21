"""
Script de migración de datos SQLite → PostgreSQL.
ArqueoTrack 2.0

Uso:
    python scripts/migrate_sqlite_to_postgres.py \\
        --sqlite arqueotrack.db \\
        --postgres postgresql://user:pass@localhost/arqueotrack

Este script:
1. Lee todos los registros de la BD SQLite existente.
2. Los inserta en PostgreSQL respetando las relaciones.
3. Reajusta las secuencias de IDs automáticos.
"""

import sys
import os
import argparse
import sqlite3

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def migrar(sqlite_path: str, postgres_url: str, dry_run: bool = False) -> None:
    """
    Migra los datos de SQLite a PostgreSQL.
    
    Args:
        sqlite_path: Ruta al fichero arqueotrack.db.
        postgres_url: URL de conexión PostgreSQL.
        dry_run: Si True, sólo muestra estadísticas sin escribir.
    """
    print(f"📂 Origen  : {sqlite_path}")
    print(f"🐘 Destino : {postgres_url}")
    print(f"🔍 Dry-run : {dry_run}")
    print()

    # ── Conectar a SQLite ─────────────────────────────────────────────────────
    if not os.path.exists(sqlite_path):
        print(f"❌ Fichero SQLite no encontrado: {sqlite_path}")
        sys.exit(1)

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    # ── Tablas en orden respetando dependencias FK ────────────────────────────
    tablas_orden = [
        'usuarios',
        'yacimientos',
        'sectores',
        'fases_proyecto',
        'hallazgos',
        'eventos',
        'comentarios',
        'invitaciones',
    ]

    estadisticas = {}
    for tabla in tablas_orden:
        cursor = sqlite_conn.execute(f"SELECT COUNT(*) FROM {tabla}")
        count = cursor.fetchone()[0]
        estadisticas[tabla] = count
        print(f"  {tabla:25s} → {count:6d} registros")

    print()

    if dry_run:
        print("✅ Análisis completado (dry-run, sin cambios).")
        return

    # ── Configurar Flask + SQLAlchemy con PostgreSQL ──────────────────────────
    os.environ['DATABASE_URL'] = postgres_url
    os.environ['FLASK_ENV'] = 'production'

    from app import create_app, db
    app = create_app('production')

    with app.app_context():
        # Crear tablas si no existen
        db.create_all()
        print("🏗️  Tablas PostgreSQL verificadas.")

        from sqlalchemy import text

        # Desactivar FK checks temporalmente
        db.session.execute(text("SET session_replication_role = 'replica';"))

        for tabla in tablas_orden:
            rows = sqlite_conn.execute(f"SELECT * FROM {tabla}").fetchall()
            if not rows:
                continue

            columnas = rows[0].keys()
            placeholders = ', '.join([f':{col}' for col in columnas])
            cols_str = ', '.join(columnas)

            for row in rows:
                db.session.execute(
                    text(f"INSERT INTO {tabla} ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"),
                    dict(row),
                )

            db.session.flush()
            print(f"  ✅ {tabla:25s} → {len(rows)} filas migradas")

        # Reactivar FK checks
        db.session.execute(text("SET session_replication_role = 'origin';"))

        # Resetear secuencias de autoincremento
        for tabla in tablas_orden:
            db.session.execute(
                text(f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), COALESCE(MAX(id), 0) + 1, false) FROM {tabla};")
            )

        db.session.commit()
        print()
        print("🎉 Migración completada exitosamente.")

    sqlite_conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrar ArqueoTrack SQLite → PostgreSQL')
    parser.add_argument('--sqlite', default='arqueotrack.db', help='Ruta al fichero SQLite')
    parser.add_argument('--postgres', required=True, help='URL PostgreSQL de destino')
    parser.add_argument('--dry-run', action='store_true', help='Sólo analizar, sin migrar')

    args = parser.parse_args()
    migrar(args.sqlite, args.postgres, args.dry_run)
