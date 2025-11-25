# Esquema de Base de Datos

Este documento detalla la estructura de la base de datos en Supabase (PostgreSQL) utilizada para orquestar el ETL y almacenar los datos procesados de gas natural.

## Diagrama Relacional

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
 └────────┬────────┘        └─────────┬────────┘        └────────┬─────────┘
          │                           │                          │
          ▼                           ▼                          ▼
     ┌──────────┐               ┌──────────┐               ┌──────────┐
     │dim_tiempo│◄──────────────│dim_tiempo│──────────────►│dim_tiempo│
     └──────────┘               └──────────┘               └──────────┘
          │
          ▼
     ┌──────────┐                                           ┌──────────┐
     │dim_campos│◄──────────────────────────────────────────│dim_campos│
     └────┬─────┘                                           └────┬─────┘
          │ N:1                                                  │
          ▼                                                      ▼
   ┌───────────────┐                                      ┌───────────────┐
   │dim_territorios│                                      │dim_territorios│
   └───────────────┘                                      └───────────────┘

                              ┌──────────────┐
                              │ ref_unidades │ (auxiliar)
                              └──────────────┘
```

---

## Tablas de Configuración ETL

### 1. `etl_sources`
Almacena la configuración maestra de cada fuente de datos. Es la fuente de verdad para el Scheduler.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `text` | **PK**. Identificador único (ej: `min_minas_gas`, `precios_bolsa`). |
| `name` | `text` | Nombre legible para humanos. |
| `active` | `boolean` | Interruptor general. Si es `false`, el scheduler ignora esta fuente. |
| `type` | `text` | Define el checker a usar: `api`, `scrape`, `complex_scraper`. |
| `schedule_cron` | `text` | Expresión CRON para la frecuencia de chequeo (ej: `0 8 * * *`). |
| `config` | `jsonb` | Parámetros específicos del checker (URL, headers, selectores CSS). |
| `storage_config` | `jsonb` | Configuración de dónde guardar los datos RAW (rutas, buckets). |
| `created_at` | `timestamptz` | Fecha de creación. |
| `updated_at` | `timestamptz` | Fecha de última modificación de la config. |

### 2. `source_check_history`
Bitácora inmutable de cada ejecución del proceso `check-updates`. Permite auditar la salud de las fuentes y detectar cuándo hubo cambios reales.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `bigint` | **PK**. Autoincremental. |
| `source_id` | `text` | **FK**. Referencia a `etl_sources.id`. |
| `status` | `enum` | Estado del chequeo: `no_change`, `changed`, `failed`. |
| `checksum` | `text` | Hash MD5 del contenido detectado (para comparar cambios). |
| `metadata` | `jsonb` | Datos variables de la ejecución (URL consultada, notas de error, método usado). |
| `created_at` | `timestamptz` | Fecha y hora exacta de la ejecución. |

---

## Tablas de Dimensiones

### 3. `dim_tiempo`
Dimensión temporal compartida por todas las tablas de hechos. Granularidad mensual con campos derivados.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `serial` | **PK**. Identificador único. |
| `fecha` | `date` | Fecha del período (UNIQUE). |
| `anio` | `smallint` | Año del registro. |
| `mes` | `smallint` | Mes (1-12) con CHECK constraint. |
| `trimestre` | `smallint` | **GENERATED**. Trimestre calculado automáticamente (1-4). |
| `semestre` | `smallint` | **GENERATED**. Semestre calculado automáticamente (1-2). |
| `nombre_mes` | `text` | Nombre del mes en español. |
| `es_proyeccion` | `boolean` | Indica si es dato proyectado vs histórico. |
| `created_at` | `timestamptz` | Fecha de creación del registro. |

### 4. `dim_territorios`
Dimensión geográfica con departamentos y municipios de Colombia.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `serial` | **PK**. Identificador único. |
| `departamento` | `text` | Nombre del departamento. |
| `municipio` | `text` | Nombre del municipio. |
| `latitud` | `numeric(10,7)` | Coordenada de latitud. |
| `longitud` | `numeric(10,7)` | Coordenada de longitud. |
| `divipola` | `text` | Código DANE DIVIPOLA. |
| `created_at` | `timestamptz` | Fecha de creación. |

**Constraint**: `UNIQUE(departamento, municipio)`

### 5. `dim_campos`
Dimensión de campos petroleros/gasíferos con información contractual.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `serial` | **PK**. Identificador único. |
| `nombre_campo` | `text` | Nombre del campo (UNIQUE). |
| `contrato` | `text` | Nombre del contrato asociado. |
| `operador` | `text` | Empresa operadora. |
| `asociados` | `text[]` | Array de empresas asociadas. |
| `participacion_estado` | `numeric(5,2)` | Porcentaje de participación estatal. |
| `territorio_id` | `int` | **FK** → `dim_territorios.id`. |
| `activo` | `boolean` | Estado del campo. |
| `created_at` | `timestamptz` | Fecha de creación. |
| `updated_at` | `timestamptz` | Fecha de última modificación. |

---

## Tablas de Referencia

### 6. `ref_unidades`
Tabla auxiliar con factores de conversión entre unidades de medida.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `serial` | **PK**. Identificador único. |
| `codigo` | `text` | Código de la unidad (UNIQUE). |
| `nombre` | `text` | Nombre completo de la unidad. |
| `factor_a_gbtud` | `numeric(18,10)` | Factor de conversión a GBTUD (unidad base). |
| `descripcion` | `text` | Descripción y notas de la unidad. |

**Valores predefinidos**:
| Código | Nombre | Factor | Descripción |
| :--- | :--- | :--- | :--- |
| `GBTUD` | Giga BTU por Día | 1.0 | Unidad base para demanda |
| `KPCD` | Kilo Pies Cúbicos por Día | 0.001 | 1 KPCD ≈ 0.001 GBTUD |
| `MPCD` | Millones Pies Cúbicos por Día | 1.0 | 1 MPCD ≈ 1 GBTUD |
| `BLS` | Barriles | NULL | Unidad de líquidos |
| `KPC` | Kilo Pies Cúbicos | 0.001 | Unidad de volumen gas |

---

## Tablas de Hechos

### 7. `fact_regalias`
**Fuente**: API Socrata ANH (j7js-yk74)  
Almacena la liquidación de regalías por campo de hidrocarburos.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `bigserial` | **PK**. Identificador único. |
| `tiempo_id` | `int` | **FK** → `dim_tiempo.id`. |
| `campo_id` | `int` | **FK** → `dim_campos.id`. |
| `tipo_produccion` | `text` | Tipo de producción (QB/P/B/I/QI). |
| `tipo_hidrocarburo` | `char(1)` | `G`=Gas, `O`=Petróleo. CHECK constraint. |
| `precio_usd` | `numeric(12,4)` | Precio del hidrocarburo en USD. |
| `porcentaje_regalia` | `numeric(5,2)` | % de producción gravable. |
| `produccion_gravable` | `numeric(18,4)` | Volumen de producción gravable. |
| `volumen_regalia` | `numeric(18,4)` | Volumen de regalías. |
| `unidad` | `text` | Unidad de medida (default: Bls/Kpc). |
| `valor_regalias_cop` | `numeric(18,2)` | Valor de regalías en COP. |
| `source_id` | `text` | **FK** → `etl_sources.id`. Trazabilidad. |
| `etl_timestamp` | `timestamptz` | Timestamp de carga ETL. |

**Índices**: `tiempo_id`, `campo_id`, `tipo_hidrocarburo`, `source_id`

### 8. `fact_demanda_gas`
**Fuente**: UPME - Anexo Proyección Demanda  
Almacena proyecciones de demanda de gas natural con múltiples dimensiones categóricas.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `bigserial` | **PK**. Identificador único. |
| `tiempo_id` | `int` | **FK** → `dim_tiempo.id`. |
| `escenario` | `text` | Escenario de proyección. CHECK: `MEDIO`, `ALTO`, `BAJO`, `IC_95`, `IC_68`. |
| `sector` | `text` | Sector de consumo. CHECK: `RESIDENCIAL`, `TERCIARIO`, `INDUSTRIAL`, `PETROQUIMICA`, `PETROLERO`, `GNV`, `TERMOELECTRICO`, `REFINERIA`. |
| `region` | `text` | Región geográfica. CHECK: `CENTRO`, `COSTA`, `CQR`, `NOROESTE`, `OCCIDENTE`, `ORIENTE`, `SUR`, `TOLIMA_GRANDE`. |
| `segmento` | `text` | Segmento de demanda. CHECK: `TOTAL`, `PETROLERO`, `TERMOELECTRICO`, `NO_TERMOELECTRICO`. |
| `nivel_agregacion` | `text` | Nivel de agregación. CHECK: `nacional`, `sectorial`, `regional`. |
| `valor_demanda_gbtud` | `numeric(18,6)` | Valor de demanda en GBTUD. |
| `source_id` | `text` | **FK** → `etl_sources.id`. Trazabilidad. |
| `etl_timestamp` | `timestamptz` | Timestamp de carga ETL. |

**Índices**: `tiempo_id`, `escenario`, `sector`, `region`, `source_id`

### 9. `fact_oferta_gas`
**Fuente**: MinMinas - Declaración de Producción  
Almacena la declaración de producción de gas por campo.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `bigserial` | **PK**. Identificador único. |
| `tiempo_id` | `int` | **FK** → `dim_tiempo.id`. |
| `campo_id` | `int` | **FK** → `dim_campos.id`. |
| `potencial_produccion` | `numeric(18,4)` | Volumen declarado de producción. |
| `unidad` | `text` | Unidad de medida (default: KPCD). |
| `potencial_gbtud` | `numeric(18,6)` | Valor normalizado a GBTUD. |
| `source_id` | `text` | **FK** → `etl_sources.id`. Trazabilidad. |
| `etl_timestamp` | `timestamptz` | Timestamp de carga ETL. |

**Índices**: `tiempo_id`, `campo_id`, `source_id`

---

## Tipos Enumerados (ENUMs)

*   **`source_update_method`**: `'api'`, `'scraping'`, `'html'`, `'archivo'`, `'complex_scraper'`
*   **`source_check_status`**: `'no_change'`, `'changed'`, `'failed'`

---

## Script de Migración

El script SQL completo para crear la base de datos se encuentra en: [init_db.sql](./init_db.sql)
