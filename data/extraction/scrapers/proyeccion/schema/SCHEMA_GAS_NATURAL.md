## Esquema local de proyección de demanda de gas natural (`proyeccion`)

Este documento describe las tablas sugeridas en Supabase para almacenar la
proyección de **demanda de gas natural** proveniente de los archivos de Series Históricas UPME.  
No modifica la documentación global de `docs/database`, solo aplica al
scraper `proyeccion`.

### 1. `fact_demanda_gas_natural`

Tabla de hechos unificada para todas las categorías de demanda de gas natural.
Todos los archivos de "Series Históricas y de Proyección de Demanda de Gas Natural"
se consolidan en esta tabla, diferenciados por la columna `categoria`.

**Nota**: El normalizador genera un único archivo CSV consolidado (`gas_natural_consolidado_normalized.csv`)
que contiene todos los registros de todas las categorías y años, facilitando la carga masiva en la base de datos.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `bigserial` | **PK** |
| `tiempo_id` | `int` | **FK** → `dim_tiempo.id` (ya definida en el esquema global) |
| `periodicidad` | `text` | `'mensual'` (principalmente) o `'anual'` |
| `categoria` | `text` | Categoría de demanda. CHECK: `'COMPRESORES'`, `'INDUSTRIAL'`, `'PETROLERO'`, `'PETROQUIMICO'`, `'RESIDENCIAL'`, `'TERCIARIO'`, `'TERMOELECTRICO'`, `'GNC_TRANSPORTE'`, `'GNL_TRANSPORTE'`, `'AGREGADO'` |
| `region` | `text` | Región geográfica (ej: `'CENTRO'`, `'COSTA ATLÁNTICA'`, `'NACIONAL'`) - NULL si es a nivel de nodo |
| `nodo` | `text` | Nodo específico (ej: `'AGUAZUL - (AGUAZUL-YOPAL)'`) - NULL si es a nivel regional |
| `escenario` | `text` | Escenario de proyección. CHECK: `'ESC_BAJO'`, `'ESC_MEDIO'`, `'ESC_ALTO'` |
| `valor` | `numeric(18,6)` | Valor de demanda en GBTUD |
| `unidad` | `text` | Unidad de medida (default: `'GBTUD'`) |
| `revision` | `text` | Etiqueta de revisión (`REV_JULIO_2024`, `REV_DIC_2023`, etc.) |
| `year_span` | `text` | Rango de años publicado (`2024-2038`, `2023-2037`, ...) |
| `sheet_name` | `text` | Nombre de la hoja Excel de origen |
| `source_file` | `text` | Nombre del archivo Excel de origen |
| `source_id` | `text` | **FK** → `etl_sources.id` (para trazabilidad ETL) |
| `etl_timestamp` | `timestamptz` | Timestamp de carga |

**Constraint sugerida** (idempotencia):

- `UNIQUE(tiempo_id, categoria, region, nodo, escenario, periodicidad, revision)`

Esto permite recargar la misma revisión sin duplicar registros y deja
espacio para futuras revisiones.

### Archivo de salida

El normalizador `normalizer_gas.py` genera un único archivo CSV consolidado:

- **Archivo**: `processed/gas-natural/gas_natural_consolidado_normalized.csv`
- **Contenido**: Todos los registros de todas las categorías, años y escenarios en un solo archivo
- **Ventaja**: Facilita la carga masiva en la base de datos y permite análisis consolidados

### Categorías procesadas

El normalizador procesa los siguientes archivos y categorías, consolidándolos en el CSV único:

| Archivo | Categoría | Descripción |
| :--- | :--- | :--- |
| `Series ... - Compresores.xlsx` | `COMPRESORES` | Demanda de gas para compresores |
| `Series ... - Industrial.xlsx` | `INDUSTRIAL` | Demanda industrial |
| `Series ... - Petrolero.xlsx` | `PETROLERO` | Demanda del sector petrolero |
| `Series ... - Petroquímico.xlsx` | `PETROQUIMICO` | Demanda petroquímica |
| `Series ... - Residencial.xlsx` | `RESIDENCIAL` | Demanda residencial |
| `Series ... - Terciario.xlsx` | `TERCIARIO` | Demanda del sector terciario |
| `Series ... - TermoEléctrico.xlsx` | `TERMOELECTRICO` | Demanda para generación termoeléctrica |
| `Series ... Comprimido (GNC) – Transporte.xlsx` | `GNC_TRANSPORTE` | Gas Natural Comprimido para transporte |
| `Series ... Licuado (GNL) – Transporte.xlsx` | `GNL_TRANSPORTE` | Gas Natural Licuado para transporte |
| `Series ... Agregada.xlsx` o `Agregado.xlsx` | `AGREGADO` | Demanda agregada total |

### Estructura de los archivos Excel

Los archivos Excel típicamente contienen:

- **Hojas**: `"Esc Alto, Medio y Bajo"`, `"Esc Med Regional"`, `"Esc Med Nodal"`
- **Columnas**: Nodos específicos (ej: `"AGUAZUL - (AGUAZUL-YOPAL)"`) o regiones (ej: `"Centro"`, `"Costa Atlántica"`)
- **Filas**: Fechas en formato `"mmm-yy"` (ej: `"dic-24"`, `"ene-25"`)
- **Valores**: Demanda en GBTUD (Gigabytes Térmicos por Día)
- **Escenarios**: Alto, Medio, Bajo (según la hoja)

### Relación con el normalizador

El módulo `normalizers/gas_natural.py` procesa todos los archivos Excel de gas natural y genera
un único CSV consolidado (`gas_natural_consolidado_normalized.csv`) con la siguiente estructura:

| Columna CSV | Mapeo a BD | Descripción |
| :--- | :--- | :--- |
| `period_key` | → `tiempo_id` | Clave de período (YYYY-MM-DD) que se resuelve usando `dim_tiempo` |
| `periodicidad` | → `periodicidad` | `'mensual'` (principalmente) o `'anual'` |
| `categoria` | → `categoria` | Extraída del nombre del archivo (COMPRESORES, INDUSTRIAL, etc.) |
| `region` | → `region` | Región geográfica (si aplica, NULL si es nodo) |
| `nodo` | → `nodo` | Nodo específico (si aplica, NULL si es regional) |
| `escenario` | → `escenario` | ESC_BAJO, ESC_MEDIO, ESC_ALTO (extraído del nombre de la hoja) |
| `valor` | → `valor` | Valor de demanda en GBTUD |
| `unidad` | → `unidad` | Siempre `'GBTUD'` |
| `revision` | → `revision` | Etiqueta de revisión (ej: REV_JULIO_2024) |
| `year_span` | → `year_span` | Rango de años publicado (ej: 2024) |
| `sheet_name` | → `sheet_name` | Nombre de la hoja Excel de origen |
| `source_file` | → `source_file` | Nombre del archivo Excel de origen |

**Proceso de carga**:

Un transformer posterior debería:

1. Leer el CSV consolidado `gas_natural_consolidado_normalized.csv`
2. Resolver `period_key` contra `dim_tiempo` para obtener `tiempo_id`
3. Insertar en `fact_demanda_gas_natural` respetando la clave única de idempotencia
4. Manejar correctamente los casos donde `region` o `nodo` pueden ser NULL
5. Asignar el `source_id` correspondiente desde `etl_sources`

### Índices

Se crean índices en:
- `tiempo_id` (para consultas temporales)
- `categoria` (para filtros por categoría)
- `escenario` (para filtros por escenario)
- `region` (para filtros por región)
- `revision` (para filtros por revisión)
- `source_id` (para trazabilidad ETL)

### Ventajas del diseño unificado

- **Una sola tabla** para todas las categorías facilita consultas agregadas
- **Un solo CSV consolidado** simplifica el proceso de carga ETL
- **Columna `categoria`** permite filtrar por tipo de demanda sin necesidad de múltiples tablas
- **Columnas `region` y `nodo`** permiten análisis a diferentes niveles geográficos
- **Constraint UNIQUE** asegura idempotencia y evita duplicados
- **Manejo mejorado de headers "Unnamed"**: El parser extrae correctamente la información de región/nodo desde headers multi-nivel y filas de datos

