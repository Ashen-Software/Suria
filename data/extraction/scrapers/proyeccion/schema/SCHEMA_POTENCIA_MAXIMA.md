## Esquema local de proyección de potencia máxima (`proyeccion`)

Este documento describe las tablas sugeridas en Supabase para almacenar la
proyección de demanda de **potencia máxima** proveniente de los anexos UPME.  
No modifica la documentación global de `docs/database`, solo aplica al
scraper `proyeccion`.

### 1. `dim_areas_electricas`

Catálogo de ámbitos/áreas utilizados en los anexos:

- `SIN`, `SIN_GCE_ME`, `SIN_GCE_ME_GD_UPME`, `SIN_GCE_ME_GD_PNUMA`
- Áreas del SIN: `CARIBE`, `ORIENTE`, `SUR`, `NORDESTE`, `ANTIOQUIA`, etc.
- Agrupaciones especiales de Generación Distribuida (`GD_UPME`, `GD_PNUMA`)

**Nota:** Esta tabla es compartida con las otras métricas (energía eléctrica, capacidad instalada).

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `serial` | **PK** |
| `codigo` | `text` | Código técnico único (ej. `SIN`, `CARIBE`, `GD_UPME`) |
| `nombre` | `text` | Nombre legible |
| `categoria` | `text` | CHECK (`'nacional'`, `'area_sin'`, `'combinado'`, `'gd'`, `'proyecto'`) |
| `descripcion` | `text` | Notas adicionales |
| `created_at` | `timestamptz` | Timestamp automático |

### 2. `fact_potencia_maxima`

Tabla de hechos para series mensuales/anuales de **potencia máxima** (MW):

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `bigserial` | **PK** |
| `tiempo_id` | `int` | **FK** → `dim_tiempo.id` (ya definida en el esquema global) |
| `periodicidad` | `text` | `'mensual'` o `'anual'` |
| `unidad` | `text` | Unidad original (`MW-mes`, `MW-año`) |
| `area_id` | `int` | **FK** → `dim_areas_electricas.id` |
| `descriptor` | `text` | Subnivel (por ejemplo nombre de área o proyecto GD) |
| `escenario` | `text` | `'ESC_BAJO'`, `'ESC_MEDIO'`, `'ESC_ALTO'`, `'IC_SUP_95'`, `'IC_INF_95'`, `'IC_SUP_68'`, `'IC_INF_68'` |
| `revision` | `text` | Etiqueta de revisión (`REV_JULIO_2025`, `REV_DIC_2023`, etc.) |
| `year_span` | `text` | Rango de años publicado (`2025-2039`, `2024-2038`, ...) |
| `valor` | `numeric(18,6)` | Valor numérico de potencia máxima en la unidad indicada |
| `sheet_name` | `text` | Nombre de la hoja Excel de origen |
| `source_file` | `text` | Nombre del archivo Excel de origen |
| `source_id` | `text` | **FK** → `etl_sources.id` (para trazabilidad ETL) |
| `etl_timestamp` | `timestamptz` | Timestamp de carga |

**Constraint sugerida** (idempotencia):

- `UNIQUE(tiempo_id, area_id, descriptor, escenario, periodicidad, revision)`

Esto permite recargar la misma revisión sin duplicar registros y deja
espacio para futuras revisiones (ej. una nueva versión 2026).

### Hojas Excel procesadas

El normalizador `normalizers/potencia_maxima.py` procesa las siguientes hojas:

- **Hoja 2**: Demanda mensual de Potencia Máxima SIN (MW-mes) - Nacional
- **Hoja 4**: Demanda anual de Potencia Máxima SIN (MW-año) - Nacional
- **Hoja 6**: Demanda mensual de potencia máxima GCE, VE, GD (MW-mes) - Combinado
- **Hoja 8**: Demanda anual de potencia máxima GCE, VE, GD (MW-año) - Combinado
- **Hoja 10**: Demanda mensual de Potencia Máxima Regional SIN (MW-mes) - Área SIN
- **Hoja 12**: Demanda anual de Potencia Máxima Regional SIN (MW-año) - Área SIN

### Relación con el normalizador

El módulo `normalizers/potencia_maxima.py` produce registros con la siguiente forma:

- `period_key` → se resuelve a `tiempo_id` usando `dim_tiempo`
- `periodicidad` → `periodicidad`
- `metric` → siempre `'potencia'`
- `unidad` → `unidad`
- `ambito` → se mapea a `dim_areas_electricas.codigo`
- `descriptor` → `descriptor`
- `escenario` → `escenario` (extraído del nombre de la hoja o columna: `ESC_BAJO`, `ESC_MEDIO`, `ESC_ALTO`, o intervalos de confianza)
- `revision` → `revision`
- `year_span` → `year_span`
- `valor` → `valor`

**Nota sobre escenarios:** El normalizador extrae el escenario de dos fuentes (en orden de prioridad):
1. **Nombre de la hoja Excel**: Si la hoja contiene "bajo", "medio" o "alto" en su nombre
2. **Nombre de la columna**: Si la columna contiene referencias a escenarios (ej: "Esc. Bajo", "Escenario Alto")
3. **Por defecto**: Si no se encuentra ningún escenario, se asigna `ESC_MEDIO`

Un transformer posterior debería:

1. Resolver/insertar los códigos en `dim_areas_electricas`.
2. Resolver `period_key` contra `dim_tiempo`.
3. Insertar en `fact_potencia_maxima` respetando la clave única de idempotencia.

### Índices

Se crean índices en:
- `tiempo_id` (para consultas temporales)
- `area_id` (para filtros por área)
- `escenario` (para filtros por escenario)
- `revision` (para filtros por revisión)
- `periodicidad` (para distinguir mensual vs anual)
- `source_id` (para trazabilidad ETL)

