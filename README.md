# 🏺 ArqueoTrack 2.0

> **Si encuentras algo… no lo muevas. Regístralo.**

ArqueoTrack es una plataforma web de gestión arqueológica para ciudadanos que realizan hallazgos inesperados y para equipos profesionales que gestionan excavaciones a gran escala.

---

## 🆕 Versiones implementadas

Este repositorio implementa las versiones **v1.0 → v4.0** del Plan de Refactorización Profesional:

### v1.0 — Fundamentos
| Mejora | Descripción |
|--------|-------------|
| **Capa de servicios** | Lógica de negocio separada de las rutas HTTP |
| **Configuración por entornos** | `DevelopmentConfig`, `TestingConfig`, `ProductionConfig` |
| **Logging estructurado** | `structlog`: consola colorida en dev, JSON en producción |
| **Alembic + Flask-Migrate** | Migraciones versionadas de base de datos |
| **Redis Cache** | Caché de consultas frecuentes con `@cache.memoize` |
| **Docker Compose** | PostgreSQL 15 + PostGIS 3.3 + Redis 7 + Flask |
| **Tests base** | pytest con fixtures, tests unitarios e integración (>70% coverage) |
| **GitHub Actions CI** | Tests + lint + build Docker automáticos |
| **Script de migración** | Traslada datos de SQLite → PostgreSQL |

### v2.0 — Institucionalización
| Mejora | Descripción |
|--------|-------------|
| **Multi-tenant** | `Institucion` con `tenant_uuid`, tipos, especialidades y verificación |
| **8 roles institucionales** | `director_general` → `estudiante` con jerarquía de permisos |
| **Campañas arqueológicas** | `Campana` con estado, fechas, presupuesto y director |
| **Audit log** | Registro inmutable de todas las operaciones CRUD |
| **Servicios** | `InstitucionService`, `CampanaService`, `AuditService` |
| **Templates v2.0** | Directorio de instituciones, gestión de miembros, detalle de campañas |

### v3.0 — Arqueología Científica
| Mejora | Descripción |
|--------|-------------|
| **Unidades Estratigráficas** | `UnidadEstratigrafica` con propiedades sedimentarias, cotas y área |
| **Matriz de Harris** | Grafo dirigido de relaciones estratigráficas + exportación SVG/GraphML |
| **Muestras y análisis** | `Muestra` + `ResultadoAnalisis` con pipeline de laboratorio |
| **HarrisService** | Construcción y validación del grafo con `networkx` |
| **Templates v3.0** | Tabla de UEs, formulario estratigráfico, Matriz Harris interactiva, detalle de muestras |

### v4.0 — Rendimiento y Escalabilidad
| Mejora | Descripción |
|--------|-------------|
| **Celery + Redis** | Tareas asíncronas: procesar imágenes, generar PDFs, recalcular estadísticas |
| **Celery Beat** | Tareas periódicas: limpieza de caché, mantenimiento |
| **Flower** | Monitor web de Celery en `http://localhost:5555` |
| **MinIO** | Almacenamiento S3-compatible para desarrollo/staging |
| **DB optimizada** | Índices GIN/GiST, vistas materializadas, búsqueda de texto completo |
| **StorageService** | Abstracción local/S3/MinIO configurable por env var |

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.11 + Flask 3.x + Blueprints |
| **ORM** | SQLAlchemy 2.x + Flask-Migrate (Alembic) |
| **Base de datos** | SQLite (desarrollo) / PostgreSQL 15 + PostGIS (producción) |
| **Caché** | Redis 7 vía Flask-Caching |
| **Autenticación** | Flask-Login + Flask-Bcrypt |
| **Formularios** | Flask-WTF + WTForms |
| **Logging** | structlog (consola / JSON) |
| **Mapas** | Leaflet.js + Leaflet.Draw |
| **Frontend** | Jinja2 + HTML/CSS + JavaScript vanilla |
| **Contenedores** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |
| **Tests** | pytest + pytest-cov + factory-boy + freezegun |
| **Tareas async** | Celery 5.x + Redis (broker/backend) + Flower |
| **Almacenamiento** | Local / AWS S3 / MinIO (configurable) |
| **Grafos** | NetworkX (Matriz de Harris) |

---

## 🗂️ Estructura del Proyecto

```
arqueotrack-2.0/
├── app/
│   ├── __init__.py              # Application factory (Flask-Migrate, Cache, Logging)
│   ├── logging_config.py        # ★ NUEVO: Logging estructurado con structlog
│   ├── forms.py                 # Formularios WTForms
│   ├── models/
│   │   ├── user.py              # Modelo Usuario
│   │   ├── yacimiento.py        # Modelo Yacimiento
│   │   ├── hallazgo.py          # Modelo Hallazgo
│   │   ├── sector.py            # Modelo Sector
│   │   ├── fase.py              # Modelo FaseProyecto
│   │   ├── evento.py            # Modelo Evento (timeline)
│   │   ├── comentario.py        # Modelo Comentario
│   │   └── invitacion.py        # Modelo Invitacion
│   ├── blueprints/
│   │   ├── auth.py              # Registro, login, logout
│   │   ├── main.py              # Dashboard, perfil, búsqueda
│   │   ├── yacimiento.py        # CRUD yacimientos
│   │   ├── hallazgo.py          # CRUD hallazgos
│   │   ├── sector.py            # CRUD sectores + mapa
│   │   ├── fase.py              # Gestión de fases
│   │   ├── evento.py            # Timeline de eventos
│   │   └── invitacion.py        # Sistema de invitaciones
│   ├── services/                # ★ Capa de servicios (v1.0-v4.0)
│   │   ├── auth_service.py      # Lógica de autenticación
│   │   ├── hallazgo_service.py  # Lógica de hallazgos + caché
│   │   ├── yacimiento_service.py# Lógica de yacimientos + caché
│   │   ├── institucion_service.py # ★ v2.0: Multi-tenant
│   │   ├── campana_service.py   # ★ v2.0: Campañas
│   │   ├── audit_service.py     # ★ v2.0: Auditoría
│   │   ├── ue_service.py        # ★ v3.0: Unidades estratigráficas
│   │   ├── harris_service.py    # ★ v3.0: Matriz de Harris
│   │   └── muestra_service.py   # ★ v3.0: Muestras y análisis
│   ├── tasks/                   # ★ v4.0: Tareas asíncronas (Celery)
│   │   ├── celery_app.py        # Configuración y factory Celery
│   │   ├── hallazgo_tasks.py    # Procesar imágenes (thumbnails)
│   │   ├── informe_tasks.py     # Generar PDF en background
│   │   └── estadisticas_tasks.py# Recalcular estadísticas
│   └── utils/                   # ★ Utils modularizados
│       ├── codes.py             # Generador de códigos únicos
│       ├── constants.py         # Constantes y sistema de permisos
│       ├── files.py             # Validación de archivos
│       ├── security.py          # Validación de URLs
│       └── time.py              # Formateo de tiempo relativo
├── config/
│   └── __init__.py              # ★ NUEVO: Configs por entorno (dev/test/prod)
├── tests/                       # ★ NUEVO: Suite de tests
│   ├── conftest.py              # Fixtures pytest
│   ├── unit/
│   │   ├── test_models.py       # Tests unitarios de modelos
│   │   └── test_services.py     # Tests unitarios de servicios
│   └── integration/
│       └── test_auth_routes.py  # Tests de integración de rutas
├── migrations/                  # Alembic (creado con flask db init)
├── scripts/
│   ├── init_db.sql              # Inicialización PostgreSQL
│   └── migrate_sqlite_to_postgres.py  # ★ NUEVO: Script de migración
├── templates/                   # Jinja2 (sin cambios desde v1)
├── static/                      # CSS/JS (sin cambios desde v1)
├── .github/workflows/ci.yml     # ★ NUEVO: GitHub Actions CI
├── docker-compose.yml           # ★ NUEVO: Infraestructura Docker
├── Dockerfile                   # ★ NUEVO: Imagen multi-stage
├── .env.example                 # ★ NUEVO: Variables documentadas
├── pytest.ini                   # ★ NUEVO: Configuración de tests
├── CHANGELOG.md                 # ★ NUEVO: Historial de cambios
├── MIGRATION.md                 # ★ NUEVO: Guía de migración
├── requirements.txt             # Dependencias actualizadas
└── run.py                       # Punto de entrada con CLI mejorado
```

---

## ⚡ Instalación Rápida (SQLite - Desarrollo)

```bash
# 1. Clonar
git clone https://github.com/tu-usuario/arqueotrack-2.0.git
cd arqueotrack-2.0

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate     # Linux/macOS
# venv\Scripts\activate      # Windows

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno
cp .env.example .env
# → DATABASE_URL=sqlite:///arqueotrack.db (por defecto)

# 5. Inicializar base de datos
flask db upgrade   # O: flask init-db

# 6. (Opcional) Cargar datos de ejemplo
flask seed-db

# 7. Arrancar
python run.py
```

Disponible en **http://localhost:5000** ✅

---

## 🐳 Instalación con Docker (PostgreSQL)

```bash
# 1. Configurar entorno
cp .env.example .env
# → Cambiar POSTGRES_PASSWORD y SECRET_KEY

# 2. Construir y arrancar (todos los servicios: Flask + Celery + Flower + DB + Redis)
docker compose up --build

# 2b. Solo almacenamiento S3 local con MinIO (perfil opcional)
docker compose --profile minio up --build

# 3. Aplicar migraciones (primera vez)
docker compose exec app flask db upgrade

# 4. Aplicar índices y vistas materializadas (v4.0, PostgreSQL)
docker compose exec postgres psql -U arqueotrack_user -d arqueotrack -f /docker-entrypoint-initdb.d/indexes_and_views.sql
```

Disponible en:
- **Aplicación**: http://localhost:5000 ✅
- **Flower (Celery monitor)**: http://localhost:5555 ✅
- **MinIO Console** (si activo): http://localhost:9001 ✅

---

## 🗄️ Migraciones de Base de Datos

```bash
# Crear nueva migración tras cambiar modelos
flask db migrate -m "descripción del cambio"

# Aplicar migraciones
flask db upgrade

# Ver historial
flask db history

# Revertir una versión
flask db downgrade
```

---

## 🧪 Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura de código
pytest --cov=app --cov-report=term-missing

# Tests en un módulo específico
pytest tests/unit/test_models.py -v

# Desde el CLI de Flask
flask test
flask test --coverage
```

---

## 📊 Hoja de Ruta

Consulta el **Plan de Refactorización Profesional** completo en `documentation/PLAN_REFACTORIZACION_ARQUEOTRACK.md`.

| Versión | Estado | Descripción |
|---------|--------|-------------|
| **v1.0** | ✅ **Completada** | Fundamentos: servicios, PostgreSQL, Docker, tests, logging |
| **v2.0** | ✅ **Completada** | Institucionalización: multi-tenant, campañas, roles granulares |
| **v3.0** | ✅ **Completada** | Arqueología científica: UEs, Matriz de Harris, muestras |
| **v4.0** | ✅ **Completada** | Rendimiento: Celery, Redis caché avanzada, CDN, MinIO |
| v5.0 | 📅 Planificada | Versionado tipo Git para datos arqueológicos |
| v6.0 | 📅 Planificada | Informes PDF profesionales |
| v7.0 | 📅 Planificada | Red social de arqueólogos |
| v8.0 | 📅 Planificada | Códigos QR + API REST documentada |
| v9.0 | 📅 Planificada | Producción: IaC (Terraform), CI/CD completo, monitoreo |

---

## 📚 Documentación

- [`MIGRATION.md`](MIGRATION.md) — Guía de migración desde v1
- [`CHANGELOG.md`](CHANGELOG.md) — Historial de cambios
- [`documentation/PLAN_REFACTORIZACION_ARQUEOTRACK.md`](documentation/PLAN_REFACTORIZACION_ARQUEOTRACK.md) — Plan completo

---

*Desarrollado originalmente para la competición First Lego League 2026.*
