# Changelog - ArqueoTrack

Todas las versiones notables se documentan en este fichero.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [5.0.0] - 2026-02 - v4.0 Rendimiento y Escalabilidad

### Añadido
- **Celery + Redis (broker/backend)**: procesamiento asíncrono de tareas pesadas con 3 colas especializadas (`default`, `informes`, `imagenes`).
- **Tareas Celery implementadas**:
  - `procesar_imagen_hallazgo`: genera thumbnails (300×300) y versión optimizada (1920px) en background.
  - `generar_informe_pdf`: genera informes PDF de yacimiento de forma asíncrona con notificación.
  - `calcular_estadisticas_yacimiento`: recalcula estadísticas complejas y guarda en caché Redis.
  - `limpiar_cache_periodico`: tarea periódica (beat) para purgar claves expiradas.
- **Flower**: monitor web de Celery en `http://localhost:5555` con autenticación básica.
- **Docker Compose ampliado**: servicios `celery`, `celery-beat`, `flower`, `minio` (perfil opcional).
- **MinIO**: almacenamiento S3-compatible para desarrollo/staging sin AWS.
- **`scripts/indexes_and_views.sql`**: índices GIN, GiST, compuestos y vistas materializadas para PostgreSQL.
  - `mv_estadisticas_yacimientos`: estadística agregada de hallazgos/sectores/fases por yacimiento.
  - `mv_estadisticas_instituciones`: agregado de miembros/yacimientos/campañas por institución.
  - Índices de texto completo en español con `unaccent`.
- **`StorageService`**: abstracción de almacenamiento (local / AWS S3 / MinIO) configurable por variable de entorno.
- **Pillow tasks**: thumbnails y optimización automática de imágenes de hallazgos.
- **`freezegun`** en testing para tests con fechas deterministas.
- **Variables de entorno nuevas**: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `FLOWER_USER`, `FLOWER_PASSWORD`, `STORAGE_BACKEND`, `AWS_*`, `MINIO_*`.

### Cambiado
- `requirements.txt`: `celery==5.4.0`, `flower==2.0.1`, `boto3==1.34.144`, `networkx==3.3` activados (ya no comentados).
- `docker-compose.yml` reescrito con servicios completos para producción-like.
- Hallazgo service: delega procesamiento de imagen a tarea Celery tras `crear()` y `actualizar()`.

---

## [4.0.0] - 2026-02 - v3.0 Arqueología Científica

### Añadido
- **Modelo `UnidadEstratigrafica`**: número UE único por yacimiento, tipo (capa/depósito/interfaz/corte/construcción/destrucción), propiedades sedimentarias (color Munsell, textura, compactación, composición), cotas y área.
- **Modelo `RelacionUE`**: grafo dirigido que expresa relaciones stratigráficas (encima/debajo/igual/corta/rellena/se_apoya_en) entre UEs.
- **Modelo `Muestra`**: código único, tipo (C14/palinología/antracología/cerámica/arqueo-botánica), trazabilidad de origen (UE, hallazgo, sector, campaña), coordenadas de recogida, datos de laboratorio.
- **Modelo `ResultadoAnalisis`**: resultados estructurados vinculados a muestra (tipo de análisis, valor, unidades, interpretación, error estadístico).
- **`HarrisService`**: construcción del grafo Harris con `networkx`, detección de ciclos, orden topológico, exportación a GraphML y JSON.
- **`UEService`**: CRUD de UEs, validación de número único, generación del siguiente número, `get_harris_json()`.
- **`MuestraService`**: CRUD de muestras, generación de códigos únicos, gestión del ciclo de vida (recogida → laboratorio → resultados).
- **Blueprint `ue`**: CRUD de UEs, gestión de relaciones Harris, API JSON `/harris/json`, exportación `.graphml`/`.json`.
- **Blueprint `muestra`**: CRUD de muestras, envío a laboratorio, registro de resultados, eliminación.
- **Templates v3.0** (`ues/`, `muestras/`):
  - `ues/listar.html`: tabla de UEs con tipos y filtros.
  - `ues/form.html`: formulario completo (datos sedimentarios + geometría + contexto).
  - `ues/detalle.html`: ficha de UE con relaciones Harris, hallazgos y muestras vinculados.
  - `ues/harris.html`: Matriz de Harris interactiva en SVG con exportación.
  - `muestras/listar.html`: tabla de muestras con estado de análisis.
  - `muestras/form.html`: formulario de muestra (origen, coordenadas, laboratorio).
  - `muestras/detalle.html`: ficha con pipeline de estado y registro de resultados.
- **`scripts/indexes_and_views.sql`**: índices v3.0 para UEs y muestras.

### Cambiado
- `app/__init__.py`: blueprints `ue_bp` y `muestra_bp` registrados.
- `app/forms.py`: `UnidadEstratigraficaForm`, `RelacionUEForm`, `MuestraForm`, `EnviarLaboratorioForm`, `ResultadoAnalisisForm`.
- `requirements.txt`: `networkx==3.3` añadido para el grafo Harris.

---

## [3.0.0] - 2026-02 - v2.0 Institucionalización

### Añadido
- **Modelo `Institucion`**: multi-tenant con `tenant_uuid`, tipo (universidad/museo/empresa/ONG/gobierno/investigación), especialidades JSON, verificación por administrador.
- **Modelo `UsuarioInstitucion`**: membresía con 8 roles institucionales jerárquicos (`director_general` → `estudiante`), fechas de alta/baja.
- **Modelo `Campana`**: campaña arqueológica vinculada a yacimiento e institución, con código, año, estado, fechas, presupuesto, financiador, director, metodología y objetivos.
- **Modelo `AuditLog`**: registro inmutable de todas las operaciones CRUD (entidad, operación, usuario, IP, datos antes/después en JSON, timestamp).
- **`InstitucionService`**: CRUD, búsqueda/filtrado, gestión de membresías y roles, verificación, permisos jerárquicos.
- **`CampanaService`**: CRUD, validación de fechas y presupuesto, cálculo de estadísticas (hallazgos, UEs, muestras por campaña).
- **`AuditService`**: registro centralizado de auditoría con soporte para IP y datos de cambio.
- **Blueprint `institucion`**: directorio público, detalle con gestión de miembros, añadir/remover/cambiar rol, API de autocompletar.
- **Blueprint `campana`**: CRUD de campañas por yacimiento, cambio de estado inline.
- **Templates v2.0** (`instituciones/`, `campanas/`):
  - `instituciones/listar.html`: directorio con búsqueda y filtros por tipo/país.
  - `instituciones/nueva.html` / `editar.html`: formularios de institución.
  - `instituciones/detalle.html`: perfil con estadísticas, gestión de miembros y roles.
  - `instituciones/mis_instituciones.html`: panel personal.
  - `campanas/listar.html`: listado de campañas por yacimiento.
  - `campanas/form.html`: formulario compartido crear/editar.
  - `campanas/detalle.html`: ficha de campaña con estadísticas y accesos rápidos.
- **`scripts/indexes_and_views.sql`**: índices v2.0 para `instituciones`, `usuario_institucion`, `campanas`.

### Cambiado
- `app/__init__.py`: blueprints `institucion_bp` y `campana_bp` registrados.
- `app/models/__init__.py`: nuevos modelos exportados.
- `app/forms.py`: `InstitucionForm`, `UnirseInstitucionForm`, `AñadirMiembroForm`, `CampanaForm`.
- `tests/unit/`: `test_v2_instituciones.py` con tests de servicios y modelos v2.0.

---

## [2.0.0] - 2026-02 - v1.0 Fundamentos

### Añadido
- **Capa de Servicios** (`app/services/`): `AuthService`, `YacimientoService`, `HallazgoService`
  — separa la lógica de negocio de las rutas HTTP.
- **Configuración por entornos** (`config/__init__.py`): `DevelopmentConfig`, `TestingConfig`, `ProductionConfig`.
- **Logging estructurado** (`app/logging_config.py`): `structlog` con salida colorida en desarrollo y JSON en producción.
- **Flask-Migrate + Alembic**: migraciones versionadas de base de datos.
- **Flask-Caching**: caché en memoria (dev) / Redis (prod) con decoradores `@cache.memoize`.
- **Docker Compose** (`docker-compose.yml`): PostgreSQL 15 + PostGIS 3.3, Redis 7, aplicación Flask.
- **Dockerfile** multi-stage con imagen de producción basada en `python:3.11-slim`.
- **Suite de tests** (`tests/`): fixtures pytest, tests unitarios (modelos, servicios, utils) y de integración (rutas HTTP). Coverage objetivo: >70%.
- **GitHub Actions CI** (`.github/workflows/ci.yml`): tests, lint (flake8) y build Docker automáticos.
- **Script de migración** (`scripts/migrate_sqlite_to_postgres.py`): transfiere datos de SQLite a PostgreSQL con soporte `--dry-run`.
- **`utils/` modularizado**: `codes.py`, `files.py`, `time.py`, `security.py`, `constants.py`.
- **Comandos CLI**: `flask init-db`, `flask seed-db`, `flask test`.
- **`.env.example`** completo con todas las variables documentadas.

### Cambiado
- `app/__init__.py` integra Flask-Migrate, Flask-Caching y logging estructurado.
- `run.py` simplificado; la lógica de negocio vive en los servicios.
- Blueprints refactorizados para delegar a la capa de servicios.
- `app/forms.py` importa las constantes desde `app/utils/constants.py`.
- `app/models/user.py` importa `tiene_permiso_rol` desde `app/utils/constants.py`.

### Sin cambios
- Toda la funcionalidad existente de la v1 (autenticación, yacimientos, hallazgos,
  sectores, fases, eventos, invitaciones) se conserva intacta.
- Templates Jinja2 y archivos estáticos sin modificaciones.
- Sistema de permisos y roles por yacimiento.

---

## [1.0.0] - 2025 - Versión inicial

- Monolito Flask refactorizado a Blueprints.
- Modelos: Usuario, Yacimiento, Hallazgo, Sector, FaseProyecto, Evento, Comentario, Invitación.
- Autenticación con Flask-Login + Flask-Bcrypt.
- Integración Leaflet.js con polígonos GeoJSON.
- Códigos alfanuméricos únicos para hallazgos.
- Sistema de invitaciones colaborativas con 5 niveles de rol.
- Desarrollado para la competición First Lego League 2026.
