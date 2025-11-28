-- Esquema específico para proyección de capacidad instalada UPME
-- ESTE ARCHIVO ES LOCAL AL SCRAPER `proyeccion` Y NO MODIFICA EL SCHEMA GLOBAL.

-- 1. Dimensión de áreas eléctricas (compartida con otras métricas)
-- Esta tabla se crea una sola vez y es compartida por todas las métricas

CREATE TABLE IF NOT EXISTS public.dim_areas_electricas (
  id SERIAL PRIMARY KEY,
  codigo TEXT NOT NULL UNIQUE,
  nombre TEXT NOT NULL,
  categoria TEXT CHECK (categoria IN ('nacional', 'area_sin', 'combinado', 'gd', 'proyecto')),
  descripcion TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.dim_areas_electricas IS 'Catálogo de ámbitos/áreas usados en las proyecciones eléctricas (SIN, áreas geográficas, GD, etc.)';

-- 2. Tabla de hechos para capacidad instalada

CREATE TABLE IF NOT EXISTS public.fact_capacidad_instalada (
  id BIGSERIAL PRIMARY KEY,
  tiempo_id INT REFERENCES public.dim_tiempo(id),
  periodicidad TEXT NOT NULL CHECK (periodicidad IN ('anual')),
  unidad TEXT NOT NULL,
  area_id INT REFERENCES public.dim_areas_electricas(id),
  descriptor TEXT,
  escenario TEXT NOT NULL CHECK (escenario IN ('ESC_BAJO', 'ESC_MEDIO', 'ESC_ALTO', 'IC_SUP_95', 'IC_INF_95', 'IC_SUP_68', 'IC_INF_68')),
  revision TEXT NOT NULL,
  year_span TEXT,
  valor NUMERIC(18, 6) NOT NULL,
  sheet_name TEXT,
  source_file TEXT,
  source_id TEXT REFERENCES public.etl_sources(id),
  etl_timestamp TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT fact_capacidad_instalada_unique UNIQUE (
    tiempo_id, 
    area_id, 
    descriptor, 
    escenario, 
    periodicidad, 
    revision
  )
);

CREATE INDEX IF NOT EXISTS idx_capacidad_instalada_tiempo ON public.fact_capacidad_instalada(tiempo_id);
CREATE INDEX IF NOT EXISTS idx_capacidad_instalada_area ON public.fact_capacidad_instalada(area_id);
CREATE INDEX IF NOT EXISTS idx_capacidad_instalada_escenario ON public.fact_capacidad_instalada(escenario);
CREATE INDEX IF NOT EXISTS idx_capacidad_instalada_revision ON public.fact_capacidad_instalada(revision);
CREATE INDEX IF NOT EXISTS idx_capacidad_instalada_source ON public.fact_capacidad_instalada(source_id);

COMMENT ON TABLE public.fact_capacidad_instalada IS 'Hechos: Proyección de capacidad instalada de generación distribuida (MW) - Fuente UPME';
COMMENT ON COLUMN public.fact_capacidad_instalada.periodicidad IS 'Periodicidad de la proyección: anual (solo disponible anualmente)';
COMMENT ON COLUMN public.fact_capacidad_instalada.unidad IS 'Unidad de medida: MW-año';
COMMENT ON COLUMN public.fact_capacidad_instalada.valor IS 'Valor de capacidad instalada en MW';
COMMENT ON COLUMN public.fact_capacidad_instalada.escenario IS 'Escenario de proyección: ESC_BAJO, ESC_MEDIO, ESC_ALTO, o intervalo de confianza (IC_SUP_95, IC_INF_95, IC_SUP_68, IC_INF_68)';
COMMENT ON COLUMN public.fact_capacidad_instalada.revision IS 'Etiqueta de revisión (ej: REV_JULIO_2025, REV_DIC_2023)';

