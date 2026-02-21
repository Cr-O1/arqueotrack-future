-- ─────────────────────────────────────────────────────────────────────────────
-- ArqueoTrack v4.0 — Índices y vistas materializadas para rendimiento
-- Ejecutar DESPUÉS de flask db upgrade / crear todas las tablas.
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Índices v1.0 ─────────────────────────────────────────────────────────────

-- Hallazgos: consultas frecuentes por yacimiento + tipo + fecha
CREATE INDEX IF NOT EXISTS idx_hallazgo_yacimiento_tipo
    ON hallazgos (yacimiento_id, tipo);

CREATE INDEX IF NOT EXISTS idx_hallazgo_yacimiento_fecha
    ON hallazgos (yacimiento_id, fecha DESC NULLS LAST);

-- Búsqueda por texto en nombre/descripción de hallazgos
CREATE INDEX IF NOT EXISTS idx_hallazgo_nombre_gin
    ON hallazgos USING gin(to_tsvector('spanish', coalesce(nombre, '')));

-- Sectores por yacimiento
CREATE INDEX IF NOT EXISTS idx_sector_yacimiento
    ON sectores (yacimiento_id);

-- Fases por yacimiento + estado
CREATE INDEX IF NOT EXISTS idx_fase_yacimiento_estado
    ON fases_proyecto (yacimiento_id, estado);

-- ── Índices v2.0 ─────────────────────────────────────────────────────────────

-- Instituciones: búsqueda por país y tipo
CREATE INDEX IF NOT EXISTS idx_institucion_pais_tipo
    ON instituciones (pais, tipo);

-- Membresías: lookup usuario → institución y viceversa
CREATE INDEX IF NOT EXISTS idx_usuario_institucion_usuario
    ON usuario_institucion (usuario_id, activo);

CREATE INDEX IF NOT EXISTS idx_usuario_institucion_inst
    ON usuario_institucion (institucion_id, activo);

-- Campañas: lookup por yacimiento + año
CREATE INDEX IF NOT EXISTS idx_campana_yacimiento_anio
    ON campanas (yacimiento_id, anio DESC);

CREATE INDEX IF NOT EXISTS idx_campana_estado
    ON campanas (estado, yacimiento_id);

-- Audit log: búsquedas frecuentes por entidad o yacimiento + fecha
CREATE INDEX IF NOT EXISTS idx_audit_entidad
    ON audit_logs (entidad_tipo, entidad_id);

CREATE INDEX IF NOT EXISTS idx_audit_yacimiento_fecha
    ON audit_logs (yacimiento_id, fecha DESC NULLS LAST)
    WHERE yacimiento_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_audit_usuario_fecha
    ON audit_logs (usuario_id, fecha DESC NULLS LAST);

-- ── Índices v3.0 ─────────────────────────────────────────────────────────────

-- UEs: lookup por yacimiento + número (único por yacimiento)
CREATE INDEX IF NOT EXISTS idx_ue_yacimiento_numero
    ON unidades_estratigraficas (yacimiento_id, numero_ue);

CREATE INDEX IF NOT EXISTS idx_ue_campana
    ON unidades_estratigraficas (campana_id)
    WHERE campana_id IS NOT NULL;

-- Relaciones Harris: grafos dirigidos — joins frecuentes en ambas direcciones
CREATE INDEX IF NOT EXISTS idx_relacion_ue_posterior
    ON relaciones_ue (ue_posterior_id);

CREATE INDEX IF NOT EXISTS idx_relacion_ue_anterior
    ON relaciones_ue (ue_anterior_id);

-- Muestras: lookup por yacimiento + estado + tipo
CREATE INDEX IF NOT EXISTS idx_muestra_yacimiento_estado
    ON muestras (yacimiento_id, estado);

CREATE INDEX IF NOT EXISTS idx_muestra_yacimiento_tipo
    ON muestras (yacimiento_id, tipo);

CREATE INDEX IF NOT EXISTS idx_muestra_ue
    ON muestras (ue_id)
    WHERE ue_id IS NOT NULL;

-- Resultados de análisis por muestra
CREATE INDEX IF NOT EXISTS idx_resultado_muestra
    ON resultados_analisis (muestra_id);

-- ── Índices espaciales PostGIS ────────────────────────────────────────────────
-- (Descomentar al activar GeoAlchemy2 y PostGIS en producción)

-- CREATE INDEX IF NOT EXISTS idx_hallazgo_geom
--     ON hallazgos USING gist(geom)
--     WHERE geom IS NOT NULL;

-- CREATE INDEX IF NOT EXISTS idx_yacimiento_geom
--     ON yacimientos USING gist(geom)
--     WHERE geom IS NOT NULL;

-- ── Vistas materializadas ─────────────────────────────────────────────────────

-- Estadísticas por yacimiento (refresco programado con Celery)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_estadisticas_yacimiento AS
SELECT
    y.id                                            AS yacimiento_id,
    y.nombre                                        AS yacimiento_nombre,
    y.estado                                        AS yacimiento_estado,
    COUNT(DISTINCT h.id)                            AS total_hallazgos,
    COUNT(DISTINCT c.id)                            AS total_campanas,
    COUNT(DISTINCT ue.id)                           AS total_ues,
    COUNT(DISTINCT m.id)                            AS total_muestras,
    COUNT(DISTINCT m.id) FILTER (
        WHERE m.estado = 'resultado_disponible'
    )                                               AS muestras_con_resultado,
    MAX(h.fecha)                                    AS ultimo_hallazgo,
    MAX(c.fecha_inicio)                             AS ultima_campana_inicio,
    NOW()                                           AS calculado_en
FROM yacimientos y
LEFT JOIN hallazgos  h  ON h.yacimiento_id  = y.id
LEFT JOIN campanas   c  ON c.yacimiento_id  = y.id
LEFT JOIN unidades_estratigraficas ue ON ue.yacimiento_id = y.id
LEFT JOIN muestras   m  ON m.yacimiento_id  = y.id
GROUP BY y.id, y.nombre, y.estado
WITH DATA;

-- Índice único en la vista materializada para consultas rápidas
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_estadisticas_yacimiento_id
    ON mv_estadisticas_yacimiento (yacimiento_id);

-- Estadísticas de muestras por tipo y estado
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_muestras_por_tipo AS
SELECT
    yacimiento_id,
    tipo,
    estado,
    COUNT(*) AS total,
    MIN(fecha_recogida) AS primera,
    MAX(fecha_recogida) AS ultima
FROM muestras
GROUP BY yacimiento_id, tipo, estado
WITH DATA;

CREATE INDEX IF NOT EXISTS idx_mv_muestras_tipo_yac
    ON mv_muestras_por_tipo (yacimiento_id, tipo);

-- ── Función para refrescar vistas (llamada desde Celery) ─────────────────────

CREATE OR REPLACE FUNCTION refrescar_estadisticas()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_estadisticas_yacimiento;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_muestras_por_tipo;
END;
$$;

-- ── Comentarios ───────────────────────────────────────────────────────────────
COMMENT ON MATERIALIZED VIEW mv_estadisticas_yacimiento IS
    'Estadísticas agregadas por yacimiento. Refrescar periódicamente con Celery beat.';

COMMENT ON FUNCTION refrescar_estadisticas() IS
    'Refresca todas las vistas materializadas de ArqueoTrack. Llamar desde task estadisticas_tasks.actualizar_estadisticas_diarias.';
