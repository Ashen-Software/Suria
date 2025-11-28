-- Esquema específico para proyección de demanda de gas natural UPME
-- ESTE ARCHIVO ES LOCAL AL SCRAPER `proyeccion` Y NO MODIFICA EL SCHEMA GLOBAL.

-- 1. Tabla de hechos para demanda de gas natural
-- Almacena todas las categorías (Compresores, Industrial, Petrolero, etc.) en una sola tabla
-- El normalizador genera un único CSV consolidado: gas_natural_consolidado_normalized.csv
-- que contiene todos los registros de todas las categorías, años y escenarios

CREATE TABLE IF NOT EXISTS public.fact_demanda_gas_natural (
  id BIGSERIAL PRIMARY KEY,
  tiempo_id INT REFERENCES public.dim_tiempo(id),
  periodicidad TEXT NOT NULL CHECK (periodicidad IN ('mensual', 'anual')),
  categoria TEXT NOT NULL CHECK (categoria IN (
    'COMPRESORES',
    'INDUSTRIAL',
    'PETROLERO',
    'PETROQUIMICO',
    'RESIDENCIAL',
    'TERCIARIO',
    'TERMOELECTRICO',
    'GNC_TRANSPORTE',
    'GNL_TRANSPORTE',
    'AGREGADO'
  )),
  region TEXT,
  nodo TEXT,
  escenario TEXT NOT NULL CHECK (escenario IN ('ESC_BAJO', 'ESC_MEDIO', 'ESC_ALTO')),
  valor NUMERIC(18, 6) NOT NULL,
  unidad TEXT NOT NULL DEFAULT 'GBTUD',
  revision TEXT NOT NULL,
  year_span TEXT,
  sheet_name TEXT,
  source_file TEXT,
  source_id TEXT REFERENCES public.etl_sources(id),
  etl_timestamp TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT fact_demanda_gas_natural_unique UNIQUE (
    tiempo_id,
    categoria,
    region,
    nodo,
    escenario,
    periodicidad,
    revision
  )
);

CREATE INDEX IF NOT EXISTS idx_demanda_gas_tiempo ON public.fact_demanda_gas_natural(tiempo_id);
CREATE INDEX IF NOT EXISTS idx_demanda_gas_categoria ON public.fact_demanda_gas_natural(categoria);
CREATE INDEX IF NOT EXISTS idx_demanda_gas_escenario ON public.fact_demanda_gas_natural(escenario);
CREATE INDEX IF NOT EXISTS idx_demanda_gas_region ON public.fact_demanda_gas_natural(region);
CREATE INDEX IF NOT EXISTS idx_demanda_gas_revision ON public.fact_demanda_gas_natural(revision);
CREATE INDEX IF NOT EXISTS idx_demanda_gas_source ON public.fact_demanda_gas_natural(source_id);

COMMENT ON TABLE public.fact_demanda_gas_natural IS 'Hechos: Proyección de demanda de gas natural por categoría (GBTUD) - Fuente UPME';
COMMENT ON COLUMN public.fact_demanda_gas_natural.categoria IS 'Categoría de demanda: Compresores, Industrial, Petrolero, Petroquímico, Residencial, Terciario, Termoeléctrico, GNC/GNL Transporte, Agregado';
COMMENT ON COLUMN public.fact_demanda_gas_natural.region IS 'Región geográfica (Centro, Costa Atlántica, etc.) - NULL si es a nivel de nodo';
COMMENT ON COLUMN public.fact_demanda_gas_natural.nodo IS 'Nodo específico (ej: AGUAZUL - (AGUAZUL-YOPAL)) - NULL si es a nivel regional';
COMMENT ON COLUMN public.fact_demanda_gas_natural.escenario IS 'Escenario de proyección: ESC_BAJO, ESC_MEDIO, ESC_ALTO';
COMMENT ON COLUMN public.fact_demanda_gas_natural.valor IS 'Valor de demanda en GBTUD';
COMMENT ON COLUMN public.fact_demanda_gas_natural.revision IS 'Etiqueta de revisión (ej: REV_JULIO_2024, REV_DIC_2023)';

