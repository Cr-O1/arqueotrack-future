-- ─── ArqueoTrack 2.0 - Inicialización PostgreSQL ────────────────────────────
-- Ejecutado automáticamente por Docker Compose en el primer arranque.

-- Habilitar extensión PostGIS (disponible en imagen postgis/postgis)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Extensión para UUIDs (preparado para v2.0+)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Extensión para búsqueda de texto completo en español (preparado para v3.0+)
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Configuración de zona horaria
SET timezone = 'UTC';
