# ArqueoTrack - Replit Agent Guide

## Overview

ArqueoTrack is a web-based archaeological management platform built with Flask. It serves two audiences: citizens who make unexpected archaeological finds, and professional teams managing large-scale excavations. The platform handles site registration, artifact tracking with unique QR codes, stratigraphic analysis (Harris Matrix), institutional multi-tenancy, lab sample management, and campaign coordination.

The project has evolved through four major versions:
- **v1.0**: Core CRUD, service layer, structured logging, caching, Docker support
- **v2.0**: Multi-tenant institutions with 8 hierarchical roles, campaigns, audit logging
- **v3.0**: Stratigraphic units (UEs), Harris Matrix graph analysis, lab samples and results
- **v4.0**: Celery async tasks, image processing, PDF generation, scheduled maintenance

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Pattern
- **Flask Application Factory** (`app/__init__.py`): `create_app()` initializes all extensions and registers blueprints. Configuration is environment-driven (`development`, `testing`, `production`).
- **Service Layer Pattern**: Business logic lives in `app/services/`, completely separated from HTTP routes in `app/blueprints/`. Routes handle request/response; services handle data operations and validation.
- **Blueprint-based routing**: Each domain area has its own blueprint (`auth`, `main`, `yacimiento`, `hallazgo`, `sector`, `evento`, `fase`, `institucion`, `campana`, `ue`, `muestra`, `invitacion`).

### Database & ORM
- **SQLAlchemy** with Flask-SQLAlchemy as the ORM. Models are in `app/models/`.
- **Default: SQLite** for development and Replit (`sqlite:///arqueotrack.db`). Configured via `DATABASE_URL` environment variable.
- **PostgreSQL** supported for production (with PostGIS for geospatial data). The `psycopg2-binary` driver is included.
- **Flask-Migrate / Alembic** for database migrations. For fresh installs, `db.create_all()` works directly.
- **Key models and their relationships**:
  - `Usuario` → owns `Yacimiento` (archaeological sites), `Hallazgo` (finds), `Evento`, `Comentario`
  - `Yacimiento` → has many `Sector`, `Hallazgo`, `FaseProyecto`, `Evento`, `Invitacion`, `Campana`, `UnidadEstratigrafica`, `Muestra`
  - `Institucion` ↔ `Usuario` via `UsuarioInstitucion` (many-to-many with roles)
  - `Campana` (campaign/season) belongs to `Yacimiento`, optionally to `Institucion`
  - `UnidadEstratigrafica` ↔ `RelacionUE` (directed graph for Harris Matrix)
  - `Muestra` → `ResultadoAnalisis` (lab sample pipeline)
  - `AuditLog` tracks all CRUD operations immutably

### Authentication & Authorization
- **Flask-Login** for session management. **Flask-Bcrypt** for password hashing.
- **Role-based permissions**: Users have roles (`arqueologo`, etc.) and institutional roles (8-level hierarchy from `director_general` to `estudiante`).
- **Per-site access control**: Site owners and invited collaborators (via `Invitacion` model with roles like `colaborador`, `asistente`, `visualizador`).
- **CSRF protection** via Flask-WTF on all forms.

### Caching
- **Flask-Caching**: Uses `SimpleCache` in development. Designed to use Redis in production (`CACHE_TYPE` configurable).
- Cache is used for statistics, site data, and Harris Matrix computations.

### Async Task Processing
- **Celery** with Redis as broker/backend for background tasks (image processing, PDF reports, statistics recalculation).
- **Celery Beat** for scheduled tasks (daily stats refresh, cache cleanup).
- Tasks defined in `app/tasks/` with separate modules for hallazgo, informe, and estadisticas tasks.

### Frontend
- **Server-side rendered** using Jinja2 templates in `templates/` directory.
- **Static assets** in `static/` (CSS in `static/css/styles.css`).
- Templates extend `base.html` which provides navbar, flash messages, and common layout.
- Forms use **WTForms** via Flask-WTF, defined in `app/forms.py`.

### Logging
- **structlog** for structured logging. Console-colored output in development, JSON in production.
- Request context (method, path, IP, user_id) is automatically added to log entries.
- Configured in `app/logging_config.py`.

### Entry Point
- `run.py` is the main entry point. It loads `.env`, creates the app, and includes CLI commands (`init-db`, `seed-db`).
- Auto-setup for Replit: creates upload directory and initializes database tables automatically.

### Project Structure
```
├── run.py                    # Entry point
├── config/                   # Environment configs (Dev/Test/Prod)
├── app/
│   ├── __init__.py          # Application factory
│   ├── logging_config.py    # Structured logging setup
│   ├── models/              # SQLAlchemy models (14 models)
│   ├── services/            # Business logic layer (8 services)
│   ├── blueprints/          # Flask route handlers (12 blueprints)
│   ├── forms.py             # WTForms definitions
│   ├── tasks/               # Celery async tasks
│   └── utils/               # Helpers (codes, files, security, time, constants)
├── templates/               # Jinja2 templates
├── static/                  # CSS, JS, images
├── tests/                   # pytest test suite
├── scripts/                 # Migration and DB scripts
└── requirements.txt         # Python dependencies
```

## External Dependencies

### Python Packages (Core)
- **Flask 3.0.3** with Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt, Flask-WTF, Flask-Migrate, Flask-Caching
- **SQLAlchemy 2.0.30** + **Alembic 1.13.1** for ORM and migrations
- **psycopg2-binary 2.9.9** for PostgreSQL connectivity
- **structlog 24.4.0** for structured logging
- **WTForms 3.1.2** + **email-validator** for form handling
- **Pillow 10.4.0** for image processing
- **reportlab 4.2.2** for PDF generation
- **networkx 3.3** for Harris Matrix graph algorithms
- **python-dotenv 1.0.1** for environment variable loading
- **flask-restx 1.3.0** (prepared for future REST API)

### Infrastructure Services
- **Redis**: Used as both cache backend and Celery broker. Not required for basic development (falls back to SimpleCache).
- **PostgreSQL + PostGIS**: Production database. SQLite works for development.
- **Celery 5.4.0** + **Flower 2.0.1**: Async task processing and monitoring. Optional for basic functionality.
- **MinIO / AWS S3**: Object storage for files (via boto3). Optional; local filesystem is the default.

### Environment Variables
- `DATABASE_URL`: Database connection string (defaults to `sqlite:///arqueotrack.db`)
- `SECRET_KEY`: Flask secret key
- `FLASK_ENV`: Environment name (`development`, `testing`, `production`)
- `REDIS_URL`: Redis connection for cache and Celery
- `UPLOAD_FOLDER`: Directory for file uploads (defaults to `uploads`)
- `LOG_LEVEL`, `LOG_FORMAT`: Logging configuration
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`: Celery configuration
- `STORAGE_BACKEND`, `AWS_*`, `MINIO_*`: Storage backend configuration