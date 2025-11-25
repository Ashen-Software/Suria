# Plan: Estructura de BD para centralización de datos de gas natural

El sistema actual tiene infraestructura ETL (`etl_sources`, `source_check_history`) pero carece de tablas para almacenar los datos procesados. Propongo un modelo estrella (star schema) con dimensiones compartidas y tablas de hechos por fuente, vinculadas a `etl_sources` para trazabilidad.

## Fuentes de Datos

| # | Fuente | Tipo | Enfoque | Periodo | Unidad |
|---|--------|------|---------|---------|--------|
| 1 | API Socrata (ANH) | API | Regalías por campo | 2010-presente | COP/USD, Bls/Kpc |
| 2 | Anexo_Proyeccion_Demanda (UPME) | XLSX | Demanda/Consumo | 2022-2036 | GBTUD |
| 3 | Declaracion_Produccion (MinMinas) | XLSX | Oferta/Producción | 2023-2032 | KPCD/MPCD |

## Steps

1. **Crear dimensión temporal `dim_tiempo`** — Compartida, granularidad mensual con campos derivados (trimestre, semestre).

2. **Crear dimensión geográfica `dim_territorios`** — Departamentos/municipios con coordenadas y código DIVIPOLA.

3. **Crear dimensión de campos `dim_campos`** — Campos petroleros/gasíferos con contrato, operador y participación estatal.

4. **Crear tabla de referencia `ref_unidades`** — Factores de conversión entre unidades (GBTUD, KPCD, MPCD, etc.).

5. **Crear tabla de hechos `fact_regalias`** — Liquidación de regalías por campo (Fuente 1: ANH).

6. **Crear tabla de hechos `fact_demanda_gas`** — Proyección de demanda con CHECK constraints para escenario/sector/región (Fuente 2: UPME).

7. **Crear tabla de hechos `fact_oferta_gas`** — Declaración de producción por campo (Fuente 3: MinMinas).

8. **Documentar esquema** en [esquema.md](./esquema.md) con descripción de campos y relaciones.

---

## Diagrama de Relaciones

```
                              ┌─────────────────┐
                              │   etl_sources   │
                              │  (config ETL)   │
                              └────────┬────────┘
                                       │ 1:N
          ┌────────────────────────────┼────────────────────────────┐
          │                            │                            │
          ▼                            ▼                            ▼
 ┌─────────────────┐        ┌──────────────────┐        ┌──────────────────┐
 │  fact_regalias  │        │ fact_demanda_gas │        │  fact_oferta_gas │
 │   (ANH API)     │        │     (UPME)       │        │   (MinMinas)     │
 └────────┬────────┘        │  CHECK constraints│        └────────┬─────────┘
          │                 │  escenario/sector │                 │
          │                 │  region/segmento  │                 │
          │                 └─────────┬─────────┘                 │
          │                           │                           │
          ▼                           ▼                           ▼
     ┌──────────┐               ┌──────────┐               ┌──────────┐
     │dim_tiempo│◄──────────────│dim_tiempo│──────────────►│dim_tiempo│
     └──────────┘               └──────────┘               └──────────┘
          │                                                       │
          ▼                                                       ▼
     ┌──────────┐                                           ┌──────────┐
     │dim_campos│◄──────────────────────────────────────────│dim_campos│
     └────┬─────┘                                           └────┬─────┘
          │ N:1                                                  │
          ▼                                                      ▼
   ┌──────────────┐                                      ┌──────────────┐
   │dim_territorios│                                      │dim_territorios│
   └──────────────┘                                      └──────────────┘

                              ┌──────────────┐
                              │ ref_unidades │ (auxiliar - sin FK)
                              └──────────────┘
```

## Relaciones entre Fuentes

| Elemento | Regalías (ANH) | Demanda (UPME) | Oferta (MinMinas) |
|----------|----------------|----------------|-------------------|
| `dim_tiempo` | ✅ FK | ✅ FK | ✅ FK |
| `dim_campos` | ✅ FK | ❌ | ✅ FK |
| `dim_territorios` | ✅ (vía campos) | ❌ | ✅ (vía campos) |
| escenario | ❌ | ✅ CHECK | ❌ |
| sector | ❌ | ✅ CHECK | ❌ |
| region | ❌ | ✅ CHECK | ❌ |

---

## Esquema SQL

```sql
-- ============================================
-- DIMENSIÓN TEMPORAL
-- ============================================

CREATE TABLE IF NOT EXISTS public.dim_tiempo (
  id SERIAL PRIMARY KEY,
  fecha DATE NOT NULL UNIQUE,
  anio SMALLINT NOT NULL,
  mes SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
  trimestre SMALLINT GENERATED ALWAYS AS (((mes - 1) / 3) + 1) STORED,
  semestre SMALLINT GENERATED ALWAYS AS (CASE WHEN mes <= 6 THEN 1 ELSE 2 END) STORED,
  nombre_mes TEXT NOT NULL,
  es_proyeccion BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tiempo_anio_mes ON public.dim_tiempo(anio, mes);
COMMENT ON TABLE public.dim_tiempo IS 'Dimensión temporal compartida - granularidad mensual';

-- ============================================
-- DIMENSIÓN GEOGRÁFICA
-- ============================================

CREATE TABLE IF NOT EXISTS public.dim_territorios (
  id SERIAL PRIMARY KEY,
  departamento TEXT NOT NULL,
  municipio TEXT NOT NULL,
  latitud NUMERIC(10, 7),
  longitud NUMERIC(10, 7),
  divipola TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(departamento, municipio)
);

COMMENT ON TABLE public.dim_territorios IS 'Dimensión geográfica - departamentos/municipios DANE';

-- ============================================
-- DIMENSIÓN CAMPOS
-- ============================================

CREATE TABLE IF NOT EXISTS public.dim_campos (
  id SERIAL PRIMARY KEY,
  nombre_campo TEXT NOT NULL UNIQUE,
  contrato TEXT,
  operador TEXT,
  asociados TEXT[],
  participacion_estado NUMERIC(5, 2),
  territorio_id INT REFERENCES public.dim_territorios(id),
  activo BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.dim_campos IS 'Dimensión de campos de hidrocarburos';

-- ============================================
-- TABLA DE REFERENCIA: UNIDADES
-- ============================================

CREATE TABLE IF NOT EXISTS public.ref_unidades (
  id SERIAL PRIMARY KEY,
  codigo TEXT NOT NULL UNIQUE,
  nombre TEXT NOT NULL,
  factor_a_gbtud NUMERIC(18, 10),
  descripcion TEXT
);

INSERT INTO public.ref_unidades (codigo, nombre, factor_a_gbtud, descripcion) VALUES
  ('GBTUD', 'Giga BTU por Día', 1.0, 'Unidad base para demanda'),
  ('KPCD', 'Kilo Pies Cúbicos por Día', 0.001, '1 KPCD ≈ 0.001 GBTUD'),
  ('MPCD', 'Millones Pies Cúbicos por Día', 1.0, '1 MPCD ≈ 1 GBTUD'),
  ('BLS', 'Barriles', NULL, 'Unidad de líquidos - sin conversión a gas'),
  ('KPC', 'Kilo Pies Cúbicos', 0.001, 'Unidad de volumen gas')
ON CONFLICT (codigo) DO NOTHING;

COMMENT ON TABLE public.ref_unidades IS 'Referencia de unidades y factores de conversión';

-- ============================================
-- TABLA DE HECHOS: REGALÍAS (Fuente 1: ANH)
-- ============================================

CREATE TABLE IF NOT EXISTS public.fact_regalias (
  id BIGSERIAL PRIMARY KEY,
  tiempo_id INT REFERENCES public.dim_tiempo(id),
  campo_id INT REFERENCES public.dim_campos(id),
  
  tipo_produccion TEXT,
  tipo_hidrocarburo CHAR(1) CHECK (tipo_hidrocarburo IN ('G', 'O')),
  
  precio_usd NUMERIC(12, 4),
  porcentaje_regalia NUMERIC(5, 2),
  produccion_gravable NUMERIC(18, 4),
  volumen_regalia NUMERIC(18, 4),
  unidad TEXT DEFAULT 'Bls/Kpc',
  valor_regalias_cop NUMERIC(18, 2),
  
  source_id TEXT REFERENCES public.etl_sources(id),
  etl_timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_regalias_tiempo ON public.fact_regalias(tiempo_id);
CREATE INDEX IF NOT EXISTS idx_regalias_campo ON public.fact_regalias(campo_id);
CREATE INDEX IF NOT EXISTS idx_regalias_tipo ON public.fact_regalias(tipo_hidrocarburo);

COMMENT ON TABLE public.fact_regalias IS 'Hechos: Liquidación de regalías por campo - Fuente ANH';

-- ============================================
-- TABLA DE HECHOS: DEMANDA GAS (Fuente 2: UPME)
-- ============================================

CREATE TABLE IF NOT EXISTS public.fact_demanda_gas (
  id BIGSERIAL PRIMARY KEY,
  tiempo_id INT REFERENCES public.dim_tiempo(id),
  
  escenario TEXT CHECK (escenario IN ('MEDIO', 'ALTO', 'BAJO', 'IC_95', 'IC_68')),
  sector TEXT CHECK (sector IN ('RESIDENCIAL', 'TERCIARIO', 'INDUSTRIAL', 'PETROQUIMICA', 'PETROLERO', 'GNV', 'TERMOELECTRICO', 'REFINERIA')),
  region TEXT CHECK (region IN ('CENTRO', 'COSTA', 'CQR', 'NOROESTE', 'OCCIDENTE', 'ORIENTE', 'SUR', 'TOLIMA_GRANDE')),
  segmento TEXT CHECK (segmento IN ('TOTAL', 'PETROLERO', 'TERMOELECTRICO', 'NO_TERMOELECTRICO')),
  nivel_agregacion TEXT CHECK (nivel_agregacion IN ('nacional', 'sectorial', 'regional')),
  
  valor_demanda_gbtud NUMERIC(18, 6),
  
  source_id TEXT REFERENCES public.etl_sources(id),
  etl_timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_demanda_tiempo ON public.fact_demanda_gas(tiempo_id);
CREATE INDEX IF NOT EXISTS idx_demanda_escenario ON public.fact_demanda_gas(escenario);
CREATE INDEX IF NOT EXISTS idx_demanda_sector ON public.fact_demanda_gas(sector);
CREATE INDEX IF NOT EXISTS idx_demanda_region ON public.fact_demanda_gas(region);

COMMENT ON TABLE public.fact_demanda_gas IS 'Hechos: Proyección de demanda de gas natural - Fuente UPME';

-- ============================================
-- TABLA DE HECHOS: OFERTA/PRODUCCIÓN (Fuente 3: MinMinas)
-- ============================================

CREATE TABLE IF NOT EXISTS public.fact_oferta_gas (
  id BIGSERIAL PRIMARY KEY,
  tiempo_id INT REFERENCES public.dim_tiempo(id),
  campo_id INT REFERENCES public.dim_campos(id),
  
  potencial_produccion NUMERIC(18, 4),
  unidad TEXT DEFAULT 'KPCD',
  potencial_gbtud NUMERIC(18, 6),
  
  source_id TEXT REFERENCES public.etl_sources(id),
  etl_timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_oferta_tiempo ON public.fact_oferta_gas(tiempo_id);
CREATE INDEX IF NOT EXISTS idx_oferta_campo ON public.fact_oferta_gas(campo_id);

COMMENT ON TABLE public.fact_oferta_gas IS 'Hechos: Declaración de producción de gas - Fuente MinMinas';
```

---

## Detalle de Campos por Fuente

### Fuente 1: API Socrata (j7js-yk74) - Regalías ANH

| Columna API | Tipo Propuesto | Descripción |
|-------------|----------------|-------------|
| `departamento` | TEXT | Departamento |
| `municipio` | TEXT | Municipio |
| `latitud` | NUMERIC(10,7) | Geolocalización (0 = sin info) |
| `longitud` | NUMERIC(10,7) | Geolocalización |
| `a_o` | SMALLINT | Año de registro |
| `mes` | SMALLINT | Mes (1-12) |
| `contrato` | TEXT | Nombre de contrato |
| `campo` | TEXT | Nombre del campo |
| `tipoprod` | TEXT | Tipo producción (QB/P/B/I/QI) |
| `tipohidrocarburo` | CHAR(1) | G=Gas, O=Petróleo |
| `preciohidrocarburousd` | NUMERIC(12,4) | Precio USD |
| `porcregalia` | NUMERIC(5,2) | % producción gravable |
| `prodgravableblskpc` | NUMERIC(18,4) | Volumen producción |
| `volumenregaliablskpc` | NUMERIC(18,4) | Volumen regalías |
| `regaliascop` | NUMERIC(18,2) | Valor en COP |

### Fuente 2: Anexo Proyección Demanda (UPME)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| fecha | DATE | Periodo mensual/anual |
| escenario | TEXT | Medio, Alto, Bajo, IC_95, IC_68 |
| segmento | TEXT | Total, Petrolero, Termoeléctrico, No Termoeléctrico |
| sector | TEXT | Residencial, Terciario, Industrial, Petroquímica, Petrolero, GNV, Termoeléctrico |
| region | TEXT | Centro, Costa, CQR, Noroeste, Occidente, Oriente, Sur, Tolima Grande |
| valor_demanda_gbtud | NUMERIC | Demanda en GBTUD |

### Fuente 3: Declaración Producción (MinMinas)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| nombre_campo | TEXT | Nombre del campo (de hoja XLSX) |
| nombre_contrato | TEXT | Contrato asociado |
| operador | TEXT | Empresa operadora |
| participacion_estado | NUMERIC(5,2) | % participación estatal |
| fecha | DATE | Año de proyección |
| potencial_produccion | NUMERIC | Volumen declarado |
| unidad | TEXT | KPCD o MPCD |
