-- ============================================================================
-- Schema para Declaraciones de Producción de Gas Natural
-- Supabase PostgreSQL Database Schema
-- ============================================================================
-- Este schema almacena la estructura jerárquica completa de declaraciones,
-- resoluciones, soportes magnéticos, cronogramas, anexos, plantillas, etc.

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLA: extractions
-- ============================================================================
-- Almacena información sobre cada ejecución del scraper/extractor
CREATE TABLE IF NOT EXISTS public.extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extraction_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_url TEXT NOT NULL,
    total_declarations INTEGER DEFAULT 0,
    total_plantillas INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.extractions IS 'Registra cada ejecución del scraper con metadata de la extracción';
COMMENT ON COLUMN public.extractions.extraction_date IS 'Fecha/hora de la extracción (del JSON)';
COMMENT ON COLUMN public.extractions.source_url IS 'URL fuente de donde se extrajo la información';

-- Índices para extractions
CREATE INDEX IF NOT EXISTS idx_extractions_date ON public.extractions(extraction_date DESC);
CREATE INDEX IF NOT EXISTS idx_extractions_source_url ON public.extractions(source_url);

-- ============================================================================
-- TABLA: declarations
-- ============================================================================
-- Almacena las declaraciones principales (ej: "Declaración 2025-2034")
CREATE TABLE IF NOT EXISTS public.declarations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extraction_id UUID NOT NULL REFERENCES public.extractions(id) ON DELETE CASCADE,
    declaration_title TEXT NOT NULL,
    total_resolutions INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Evitar duplicados en la misma extracción
    UNIQUE(extraction_id, declaration_title)
);

COMMENT ON TABLE public.declarations IS 'Declaraciones de producción de gas natural por período';
COMMENT ON COLUMN public.declarations.declaration_title IS 'Título completo de la declaración (ej: "Declaración de Producción de Gas Natural 2025 - 2034")';

-- Índices para declarations
CREATE INDEX IF NOT EXISTS idx_declarations_extraction_id ON public.declarations(extraction_id);
CREATE INDEX IF NOT EXISTS idx_declarations_title ON public.declarations(declaration_title);

-- ============================================================================
-- TABLA: resolutions
-- ============================================================================
-- Almacena las resoluciones asociadas a cada declaración
CREATE TABLE IF NOT EXISTS public.resolutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    declaration_id UUID NOT NULL REFERENCES public.declarations(id) ON DELETE CASCADE,
    number TEXT,
    date DATE,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    extracted_data JSONB, -- Para almacenar datos extraídos del Excel (si se analiza)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.resolutions IS 'Resoluciones asociadas a cada declaración';
COMMENT ON COLUMN public.resolutions.number IS 'Número de la resolución (ej: "00739", "01281")';
COMMENT ON COLUMN public.resolutions.date IS 'Fecha de la resolución';
COMMENT ON COLUMN public.resolutions.extracted_data IS 'Datos extraídos del Excel si se analizó (JSONB)';

-- Índices para resolutions
CREATE INDEX IF NOT EXISTS idx_resolutions_declaration_id ON public.resolutions(declaration_id);
CREATE INDEX IF NOT EXISTS idx_resolutions_number ON public.resolutions(number);
CREATE INDEX IF NOT EXISTS idx_resolutions_date ON public.resolutions(date);

-- ============================================================================
-- TABLA: soporte_magnetico
-- ============================================================================
-- Almacena los soportes magnéticos (archivos Excel) asociados a resoluciones
CREATE TABLE IF NOT EXISTS public.soporte_magnetico (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resolution_id UUID NOT NULL REFERENCES public.resolutions(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    local_path TEXT, -- Ruta local del archivo descargado (si aplica)
    file_size_bytes BIGINT, -- Tamaño en bytes
    file_size_mb NUMERIC(10, 2), -- Tamaño en MB
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.soporte_magnetico IS 'Archivos Excel/soportes magnéticos asociados a resoluciones';
COMMENT ON COLUMN public.soporte_magnetico.local_path IS 'Ruta local del archivo descargado en el servidor';
COMMENT ON COLUMN public.soporte_magnetico.file_size_bytes IS 'Tamaño del archivo en bytes';

-- Índices para soporte_magnetico
CREATE INDEX IF NOT EXISTS idx_soporte_magnetico_resolution_id ON public.soporte_magnetico(resolution_id);
CREATE INDEX IF NOT EXISTS idx_soporte_magnetico_url ON public.soporte_magnetico(url);

-- ============================================================================
-- TABLA: cronogramas
-- ============================================================================
-- Almacena cronogramas asociados a declaraciones (opcional, uno por declaración)
CREATE TABLE IF NOT EXISTS public.cronogramas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    declaration_id UUID NOT NULL REFERENCES public.declarations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Una declaración puede tener un solo cronograma
    UNIQUE(declaration_id)
);

COMMENT ON TABLE public.cronogramas IS 'Cronogramas asociados a declaraciones';
COMMENT ON COLUMN public.cronogramas.title IS 'Título del cronograma';

-- Índices para cronogramas
CREATE INDEX IF NOT EXISTS idx_cronogramas_declaration_id ON public.cronogramas(declaration_id);

-- ============================================================================
-- TABLA: anexos
-- ============================================================================
-- Almacena anexos asociados a declaraciones (puede haber múltiples)
CREATE TABLE IF NOT EXISTS public.anexos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    declaration_id UUID NOT NULL REFERENCES public.declarations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.anexos IS 'Anexos asociados a declaraciones (puede haber múltiples)';

-- Índices para anexos
CREATE INDEX IF NOT EXISTS idx_anexos_declaration_id ON public.anexos(declaration_id);

-- ============================================================================
-- TABLA: acceso_sistema
-- ============================================================================
-- Almacena información de acceso a sistemas (opcional, uno por declaración)
CREATE TABLE IF NOT EXISTS public.acceso_sistema (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    declaration_id UUID NOT NULL REFERENCES public.declarations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Una declaración puede tener un solo acceso a sistema
    UNIQUE(declaration_id)
);

COMMENT ON TABLE public.acceso_sistema IS 'Enlaces de acceso a sistemas de declaración';
COMMENT ON COLUMN public.acceso_sistema.title IS 'Título del enlace (ej: "Acceso al Sistema de Declaración de Gas")';

-- Índices para acceso_sistema
CREATE INDEX IF NOT EXISTS idx_acceso_sistema_declaration_id ON public.acceso_sistema(declaration_id);

-- ============================================================================
-- TABLA: plantillas_declaracion
-- ============================================================================
-- Almacena grupos de plantillas de cargue (ej: "Plantillas de cargue Declaración 2021-2030")
CREATE TABLE IF NOT EXISTS public.plantillas_declaracion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extraction_id UUID NOT NULL REFERENCES public.extractions(id) ON DELETE CASCADE,
    declaration_title TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.plantillas_declaracion IS 'Grupos de plantillas de cargue para declaraciones';

-- Índices para plantillas_declaracion
CREATE INDEX IF NOT EXISTS idx_plantillas_declaracion_extraction_id ON public.plantillas_declaracion(extraction_id);

-- ============================================================================
-- TABLA: plantillas
-- ============================================================================
-- Almacena plantillas individuales (OPERADOR, ASOCIADO) asociadas a grupos
CREATE TABLE IF NOT EXISTS public.plantillas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plantilla_declaracion_id UUID NOT NULL REFERENCES public.plantillas_declaracion(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('OPERADOR', 'ASOCIADO')),
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.plantillas IS 'Plantillas individuales de cargue (OPERADOR o ASOCIADO)';
COMMENT ON COLUMN public.plantillas.type IS 'Tipo de plantilla: OPERADOR o ASOCIADO';

-- Índices para plantillas
CREATE INDEX IF NOT EXISTS idx_plantillas_plantilla_declaracion_id ON public.plantillas(plantilla_declaracion_id);
CREATE INDEX IF NOT EXISTS idx_plantillas_type ON public.plantillas(type);

-- ============================================================================
-- TRIGGERS: Actualización automática de updated_at
-- ============================================================================
-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger a todas las tablas
CREATE TRIGGER update_extractions_updated_at BEFORE UPDATE ON public.extractions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_declarations_updated_at BEFORE UPDATE ON public.declarations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resolutions_updated_at BEFORE UPDATE ON public.resolutions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_soporte_magnetico_updated_at BEFORE UPDATE ON public.soporte_magnetico
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cronogramas_updated_at BEFORE UPDATE ON public.cronogramas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_anexos_updated_at BEFORE UPDATE ON public.anexos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_acceso_sistema_updated_at BEFORE UPDATE ON public.acceso_sistema
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plantillas_declaracion_updated_at BEFORE UPDATE ON public.plantillas_declaracion
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plantillas_updated_at BEFORE UPDATE ON public.plantillas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- FUNCIONES: Helpers para consultas comunes
-- ============================================================================

-- Función para obtener el resumen completo de una extracción
CREATE OR REPLACE FUNCTION get_extraction_summary(extraction_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'extraction', row_to_json(e.*)::jsonb,
        'declarations_count', COUNT(DISTINCT d.id),
        'resolutions_count', COUNT(DISTINCT r.id),
        'soportes_count', COUNT(DISTINCT sm.id),
        'plantillas_count', COUNT(DISTINCT pd.id)
    )
    INTO result
    FROM public.extractions e
    LEFT JOIN public.declarations d ON d.extraction_id = e.id
    LEFT JOIN public.resolutions r ON r.declaration_id = d.id
    LEFT JOIN public.soporte_magnetico sm ON sm.resolution_id = r.id
    LEFT JOIN public.plantillas_declaracion pd ON pd.extraction_id = e.id
    WHERE e.id = extraction_uuid
    GROUP BY e.id;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_extraction_summary(UUID) IS 'Obtiene un resumen completo de una extracción con conteos';

-- ============================================================================
-- VISTAS: Vistas útiles para consultas
-- ============================================================================

-- Vista completa de declaraciones con metadata
CREATE OR REPLACE VIEW vw_declarations_complete AS
SELECT 
    d.id,
    d.declaration_title,
    d.total_resolutions,
    e.extraction_date,
    e.source_url,
    COUNT(DISTINCT r.id) as resolutions_count,
    COUNT(DISTINCT sm.id) as soportes_count,
    COUNT(DISTINCT a.id) as anexos_count,
    CASE WHEN c.id IS NOT NULL THEN true ELSE false END as has_cronograma,
    CASE WHEN ac.id IS NOT NULL THEN true ELSE false END as has_acceso_sistema,
    d.created_at,
    d.updated_at
FROM public.declarations d
JOIN public.extractions e ON e.id = d.extraction_id
LEFT JOIN public.resolutions r ON r.declaration_id = d.id
LEFT JOIN public.soporte_magnetico sm ON sm.resolution_id = r.id
LEFT JOIN public.anexos a ON a.declaration_id = d.id
LEFT JOIN public.cronogramas c ON c.declaration_id = d.id
LEFT JOIN public.acceso_sistema ac ON ac.declaration_id = d.id
GROUP BY d.id, d.declaration_title, d.total_resolutions, e.extraction_date, e.source_url, c.id, ac.id, d.created_at, d.updated_at;

COMMENT ON VIEW vw_declarations_complete IS 'Vista completa de declaraciones con conteos y metadata';

-- Vista de resoluciones con sus soportes
CREATE OR REPLACE VIEW vw_resolutions_with_soportes AS
SELECT 
    r.id,
    r.number,
    r.date,
    r.title,
    r.url,
    d.declaration_title,
    COUNT(DISTINCT sm.id) as soportes_count,
    jsonb_agg(
        jsonb_build_object(
            'id', sm.id,
            'title', sm.title,
            'url', sm.url,
            'file_size_mb', sm.file_size_mb
        ) ORDER BY sm.created_at
    ) FILTER (WHERE sm.id IS NOT NULL) as soportes
FROM public.resolutions r
JOIN public.declarations d ON d.id = r.declaration_id
LEFT JOIN public.soporte_magnetico sm ON sm.resolution_id = r.id
GROUP BY r.id, r.number, r.date, r.title, r.url, d.declaration_title;

COMMENT ON VIEW vw_resolutions_with_soportes IS 'Vista de resoluciones con sus soportes magnéticos agrupados';

-- ============================================================================
-- POLÍTICAS RLS (Row Level Security) - OPCIONAL
-- ============================================================================
-- Descomentar si necesitas habilitar RLS en Supabase

-- ALTER TABLE public.extractions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.declarations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.resolutions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.soporte_magnetico ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.cronogramas ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.anexos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.acceso_sistema ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.plantillas_declaracion ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.plantillas ENABLE ROW LEVEL SECURITY;

-- Ejemplo de política para lectura pública (ajustar según necesidades):
-- CREATE POLICY "Allow public read access" ON public.extractions
--     FOR SELECT USING (true);

-- ============================================================================
-- ÍNDICES ADICIONALES PARA OPTIMIZACIÓN
-- ============================================================================

-- Índices compuestos para consultas comunes
CREATE INDEX IF NOT EXISTS idx_resolutions_declaration_number ON public.resolutions(declaration_id, number);
CREATE INDEX IF NOT EXISTS idx_soporte_resolution_url ON public.soporte_magnetico(resolution_id, url);

-- Índice GIN para búsqueda en JSONB
CREATE INDEX IF NOT EXISTS idx_resolutions_extracted_data ON public.resolutions USING GIN(extracted_data);

-- ============================================================================
-- FIN DEL SCHEMA
-- ============================================================================

