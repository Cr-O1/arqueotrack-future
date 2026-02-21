# Guía de Migración - ArqueoTrack 1.x → 2.0

Esta guía explica cómo migrar una instalación existente de ArqueoTrack a la nueva versión 2.0.

---

## Opción A: Mantener SQLite (desarrollo / Replit)

La v2.0 es **retrocompatible con SQLite** para entornos de desarrollo.
No es necesario cambiar nada en la base de datos.

```bash
# 1. Clonar el nuevo repositorio
git clone https://github.com/tu-usuario/arqueotrack-2.0.git
cd arqueotrack-2.0

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate

# 3. Instalar dependencias (nuevas: structlog, flask-migrate, flask-caching, etc.)
pip install -r requirements.txt

# 4. Copiar tu .env o configurar variables
cp .env.example .env
# → Ajusta DATABASE_URL=sqlite:///arqueotrack.db

# 5. Copiar la base de datos existente
cp ../arqueotrack/arqueotrack.db .

# 6. Aplicar migraciones (Alembic detectará que las tablas ya existen)
flask db stamp head

# 7. Arrancar
python run.py
```

---

## Opción B: Migrar a PostgreSQL (producción)

### Prerrequisitos
- PostgreSQL 15+ con extensión PostGIS instalada.
- O usar Docker Compose (recomendado).

### Pasos con Docker Compose

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# → Ajusta POSTGRES_PASSWORD y SECRET_KEY

# 2. Arrancar la infraestructura
docker compose up postgres redis -d

# 3. Analizar la migración (dry-run)
python scripts/migrate_sqlite_to_postgres.py \
    --sqlite ../arqueotrack/arqueotrack.db \
    --postgres postgresql://arqueotrack_user:pass@localhost/arqueotrack \
    --dry-run

# 4. Ejecutar la migración
python scripts/migrate_sqlite_to_postgres.py \
    --sqlite ../arqueotrack/arqueotrack.db \
    --postgres postgresql://arqueotrack_user:pass@localhost/arqueotrack

# 5. Aplicar migraciones Alembic
DATABASE_URL=postgresql://arqueotrack_user:pass@localhost/arqueotrack flask db stamp head

# 6. Arrancar la aplicación completa
docker compose up --build
```

### Verificación post-migración

```bash
# Ejecutar suite de tests contra la nueva instancia
DATABASE_URL=postgresql://... pytest --cov=app -v

# Comprobar que el número de registros coincide
python scripts/migrate_sqlite_to_postgres.py \
    --sqlite arqueotrack.db \
    --postgres postgresql://... \
    --dry-run
```

---

## Cambios en el código propio

Si has personalizado la v1, estos son los cambios a tener en cuenta:

### Imports que cambiaron

| Antes (v1) | Ahora (v2.0) |
|---|---|
| `from app.utils import generar_codigo_unico` | `from app.utils.codes import generar_codigo_unico` |
| `from app.utils import allowed_file` | `from app.utils.files import allowed_file` |
| `from app.utils import time_ago` | `from app.utils.time import time_ago` |
| `from app.utils import is_safe_url` | `from app.utils.security import is_safe_url` |
| `from app.utils import TIPOS_HALLAZGO, ...` | `from app.utils.constants import TIPOS_HALLAZGO, ...` |
| `from config import get_config` | `from config import get_config` *(sin cambios)* |

> **Nota**: `app/utils/__init__.py` re-exporta todo para compatibilidad:
> `from app.utils import generar_codigo_unico` sigue funcionando.

### Lógica de negocio

La lógica de negocio ahora vive en `app/services/`:

```python
# Antes (en blueprint):
hallazgo = Hallazgo(user_id=..., ...)
db.session.add(hallazgo)
db.session.commit()

# Ahora (en blueprint):
from app.services.hallazgo_service import HallazgoService
hallazgo = HallazgoService.crear(user_id=..., yacimiento_id=..., datos={...})
```

---

## Variables de entorno nuevas

| Variable | Descripción | Default |
|---|---|---|
| `LOG_FORMAT` | `console` (dev) o `json` (prod) | `console` |
| `LOG_LEVEL` | Nivel de logging | `DEBUG` (dev) / `INFO` (prod) |
| `REDIS_URL` | URL de Redis para caché | `redis://localhost:6379/0` |

---

## Resolución de problemas

**Error: `ModuleNotFoundError: No module named 'structlog'`**  
→ `pip install -r requirements.txt`

**Error: `sqlalchemy.exc.OperationalError` al conectar a PostgreSQL**  
→ Verificar que `DATABASE_URL` está correctamente configurado y PostgreSQL está en marcha.

**Los tests fallan por `WTF_CSRF_ENABLED`**  
→ Asegúrate de que `FLASK_ENV=testing`. La configuración `TestingConfig` desactiva CSRF automáticamente.
