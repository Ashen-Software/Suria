# Esquema de Base de Datos

Estructura de la base de datos en Supabase (PostgreSQL) para el sistema ETL de datos energéticos.

## Diagrama Relacional

```
                              ┌─────────────────┐
                              │   etl_sources   │
                              └────────┬────────┘
                                       │ 1:N
    ┌──────────────┬───────────────────┼───────────────────┬──────────────────┐
    │              │                   │                   │                  │
    ▼              ▼                   ▼                   ▼                  ▼
┌─────────┐  ┌───────────────┐  ┌─────────────┐  ┌────────────┐  ┌─────────────────┐
│fact_    │  │fact_demanda_  │  │fact_energia_│  │fact_poten- │  │fact_capacidad_  │
│regalias │  │ gas_natural   │  │  electrica  │  │cia_maxima  │  │   instalada     │
│ (ANH)   │  │   (UPME)      │  │   (UPME)    │  │  (UPME)    │  │     (UPME)      │
└────┬────┘  └───────┬───────┘  └──────┬──────┘  └─────┬──────┘  └────────┬────────┘
     │               │                 │               │                  │
     └───────────────┴────────┬────────┴───────────────┴──────────────────┘
                              ▼
                       ┌──────────────┐
                       │  dim_tiempo  │
                       └──────────────┘

┌──────────────────┐    ┌───────────────┐    ┌──────────────┐
│dim_areas_electric│    │  dim_campos   │───►│dim_territorios│
└──────────────────┘    └───────────────┘    └──────────────┘

┌──────────────┐    ┌────────────────┐    ┌──────────────────────┐
│ ref_unidades │    │dim_resoluciones│    │fact_participacion_   │
└──────────────┘    └────────────────┘    │       campo          │
                                          └──────────────────────┘
```

---

## Tablas de Configuración ETL

### `etl_sources`

Configuración maestra de cada fuente de datos.

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `text` | **PK**. Identificador único. |
| `name` | `text` | Nombre legible. |
| `active` | `boolean` | Activar/desactivar fuente. |
| `type` | `text` | Tipo: `api`, `scrape`, `complex_scraper`. |
| `schedule_cron` | `text` | Expresión CRON. |
| `config` | `jsonb` | Configuración del checker. |
| `storage_config` | `jsonb` | Configuración de almacenamiento. |

### `source_check_history`

Bitácora de ejecuciones del proceso `check-updates`.

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `bigint` | **PK**. |
| `source_id` | `text` | **FK** → `etl_sources.id`. |
| `status` | `enum` | `no_change`, `changed`, `failed`. |
| `checksum` | `text` | Hash MD5 del contenido. |
| `metadata` | `jsonb` | Datos de la ejecución. |

---

## Tablas de Dimensiones

### `dim_tiempo`

Dimensión temporal compartida. Granularidad mensual.

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `serial` | **PK**. |
| `fecha` | `date` | Fecha del período (UNIQUE). |
| `anio` | `smallint` | Año. |
| `mes` | `smallint` | Mes (1-12). |
| `trimestre` | `smallint` | **GENERATED**. (1-4). |
| `semestre` | `smallint` | **GENERATED**. (1-2). |
| `nombre_mes` | `text` | Nombre en español. |
| `es_proyeccion` | `boolean` | Dato proyectado vs histórico. |

### `dim_territorios`

Dimensión geográfica con departamentos y municipios.

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `serial` | **PK**. |
| `departamento` | `text` | Nombre del departamento. |
| `municipio` | `text` | Nombre del municipio. |
| `latitud` | `numeric(10,7)` | Coordenada. |
| `longitud` | `numeric(10,7)` | Coordenada. |
| `divipola` | `text` | Código DANE DIVIPOLA. |

### `dim_campos`

Dimensión de campos petroleros/gasíferos.

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `serial` | **PK**. |
| `nombre_campo` | `text` | Nombre del campo (UNIQUE). |
| `contrato` | `text` | Contrato asociado. |
| `operador` | `text` | Empresa operadora. |
| `asociados` | `text[]` | Empresas asociadas. |
| `participacion_estado` | `numeric(5,2)` | % participación estatal. |
| `territorio_id` | `int` | **FK** → `dim_territorios.id`. |
| `activo` | `boolean` | Estado del campo. |

### `dim_areas_electricas`

Catálogo de ámbitos/áreas para proyecciones eléctricas.

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `serial` | **PK**. |
| `codigo` | `text` | Código único. |
| `nombre` | `text` | Nombre del área. |
| `categoria` | `text` | `nacional`, `area_sin`, `combinado`, `gd`, `proyecto`. |
| `descripcion` | `text` | Descripción. |

### `dim_resoluciones`

Resoluciones MinMinas con periodos de vigencia.

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `serial` | **PK**. |
| `numero_resolucion` | `text` | Número de resolución (UNIQUE). |
| `fecha_resolucion` | `date` | Fecha de emisión. |
| `periodo_desde` | `date` | Inicio de vigencia. |
| `periodo_hasta` | `date` | Fin de vigencia. |
| `url_pdf` | `text` | Enlace al PDF. |
| `url_soporte_magnetico` | `text` | Enlace a anexos. |

---

## Tablas de Referencia

### `ref_unidades`

Factores de conversión entre unidades de medida.

| Código | Nombre | Factor a GBTUD | Descripción |
|:-------|:-------|:---------------|:------------|
| `GBTUD` | Giga BTU por Día | 1.0 | Unidad base demanda |
| `KPCD` | Kilo Pies Cúbicos por Día | 0.001 | 1 KPCD ≈ 0.001 GBTUD |
| `MPCD` | Millones Pies Cúbicos por Día | 1.0 | 1 MPCD ≈ 1 GBTUD |
| `BLS` | Barriles | NULL | Unidad de líquidos |
| `KPC` | Kilo Pies Cúbicos | 0.001 | Volumen gas |

---

## Tablas de Hechos

### `fact_regalias`

**Fuente**: API Socrata ANH (j7js-yk74)

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `bigserial` | **PK**. |
| `tiempo_id` | `int` | **FK** → `dim_tiempo.id`. |
| `campo_id` | `int` | **FK** → `dim_campos.id`. |
| `tipo_produccion` | `text` | Tipo (QB/P/B/I/QI). |
| `tipo_hidrocarburo` | `char(1)` | `G`=Gas, `O`=Petróleo. |
| `precio_usd` | `numeric(12,4)` | Precio USD. |
| `porcentaje_regalia` | `numeric(5,2)` | % gravable. |
| `produccion_gravable` | `numeric(18,4)` | Volumen producción. |
| `volumen_regalia` | `numeric(18,4)` | Volumen regalías. |
| `valor_regalias_cop` | `numeric(18,2)` | Valor en COP. |

### `fact_demanda_gas_natural`

**Fuente**: UPME - Proyección de Demanda Gas Natural

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `bigserial` | **PK**. |
| `tiempo_id` | `int` | **FK** → `dim_tiempo.id`. |
| `periodicidad` | `text` | `mensual`, `anual`. |
| `categoria` | `text` | `COMPRESORES`, `INDUSTRIAL`, `PETROLERO`, `PETROQUIMICO`, `RESIDENCIAL`, `TERCIARIO`, `TERMOELECTRICO`, `GNC_TRANSPORTE`, `GNL_TRANSPORTE`, `AGREGADO`. |
| `region` | `text` | Región geográfica. |
| `nodo` | `text` | Nodo específico. |
| `escenario` | `text` | `ESC_BAJO`, `ESC_MEDIO`, `ESC_ALTO`. |
| `valor` | `numeric(18,6)` | Valor en GBTUD. |
| `revision` | `text` | Etiqueta de revisión. |

### `fact_energia_electrica`

**Fuente**: UPME - Proyección de Demanda Energía Eléctrica

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `bigserial` | **PK**. |
| `tiempo_id` | `int` | **FK** → `dim_tiempo.id`. |
| `periodicidad` | `text` | `mensual`, `anual`. |
| `unidad` | `text` | `GWh-mes`, `GWh-año`. |
| `area_id` | `int` | **FK** → `dim_areas_electricas.id`. |
| `descriptor` | `text` | Descriptor adicional. |
| `escenario` | `text` | `ESC_BAJO`, `ESC_MEDIO`, `ESC_ALTO`, `IC_SUP_95`, `IC_INF_95`, `IC_SUP_68`, `IC_INF_68`. |
| `revision` | `text` | Etiqueta de revisión. |
| `valor` | `numeric(18,6)` | Valor en GWh. |

### `fact_potencia_maxima`

**Fuente**: UPME - Proyección de Potencia Máxima

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `bigserial` | **PK**. |
| `tiempo_id` | `int` | **FK** → `dim_tiempo.id`. |
| `periodicidad` | `text` | `mensual`, `anual`. |
| `unidad` | `text` | `MW-mes`, `MW-año`. |
| `area_id` | `int` | **FK** → `dim_areas_electricas.id`. |
| `descriptor` | `text` | Descriptor adicional. |
| `escenario` | `text` | `ESC_BAJO`, `ESC_MEDIO`, `ESC_ALTO`, `IC_SUP_95`, `IC_INF_95`, `IC_SUP_68`, `IC_INF_68`. |
| `revision` | `text` | Etiqueta de revisión. |
| `valor` | `numeric(18,6)` | Valor en MW. |

### `fact_capacidad_instalada`

**Fuente**: UPME - Proyección de Capacidad Instalada GD

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `bigserial` | **PK**. |
| `tiempo_id` | `int` | **FK** → `dim_tiempo.id`. |
| `periodicidad` | `text` | `anual` (solo anual). |
| `unidad` | `text` | `MW-año`. |
| `area_id` | `int` | **FK** → `dim_areas_electricas.id`. |
| `descriptor` | `text` | Descriptor adicional. |
| `escenario` | `text` | `ESC_BAJO`, `ESC_MEDIO`, `ESC_ALTO`, `IC_SUP_95`, `IC_INF_95`, `IC_SUP_68`, `IC_INF_68`. |
| `revision` | `text` | Etiqueta de revisión. |
| `valor` | `numeric(18,6)` | Valor en MW. |

### `fact_oferta_gas`

**Fuente**: MinMinas - Declaración de Producción

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `bigserial` | **PK**. |
| `tiempo_id` | `int` | **FK** → `dim_tiempo.id`. |
| `campo_id` | `int` | **FK** → `dim_campos.id`. |
| `resolucion_id` | `int` | **FK** → `dim_resoluciones.id`. |
| `tipo_produccion` | `text` | `PTDV`, `PC_CONTRATOS`, `PC_EXPORTACIONES`, `PP`, `GAS_OPERACION`, `CIDV`. |
| `operador` | `text` | Operador. |
| `es_operador_campo` | `boolean` | ¿Es operador principal? |
| `es_participacion_estado` | `boolean` | ¿Es parte del Estado? |
| `valor_gbtud` | `numeric(18,6)` | Valor normalizado. |
| `poder_calorifico_btu_pc` | `numeric(12,4)` | BTU/PC del campo. |

### `fact_participacion_campo`

**Fuente**: MinMinas - Participación por resolución

| Columna | Tipo | Descripción |
|:--------|:-----|:------------|
| `id` | `bigserial` | **PK**. |
| `campo_id` | `int` | **FK** → `dim_campos.id`. |
| `resolucion_id` | `int` | **FK** → `dim_resoluciones.id`. |
| `periodo_desde` | `date` | Inicio del periodo. |
| `periodo_hasta` | `date` | Fin del periodo. |
| `asociado` | `text` | Empresa asociada. |
| `participacion_pct` | `numeric(5,2)` | % participación. |
| `estado_pct` | `numeric(5,2)` | % Estado. |

---

## Tipos Enumerados

- **`source_update_method`**: `'api'`, `'scraping'`, `'html'`, `'archivo'`, `'complex_scraper'`
- **`source_check_status`**: `'no_change'`, `'changed'`, `'failed'`

---

## Script de Migración

Ver: [init_db.sql](./init_db.sql)
