## Esquema local de proyección de capacidad instalada (`proyeccion`)

Este documento describe las tablas sugeridas en Supabase para almacenar la
proyección de **capacidad instalada de generación distribuida** proveniente de los anexos UPME.  
No modifica la documentación global de `docs/database`, solo aplica al
scraper `proyeccion`.

### 1. `dim_areas_electricas`

Catálogo de ámbitos/áreas utilizados en los anexos:

- `SIN`, `SIN_GCE_ME`, `SIN_GCE_ME_GD_UPME`, `SIN_GCE_ME_GD_PNUMA`
- Áreas del SIN: `CARIBE`, `ORIENTE`, `SUR`, `NORDESTE`, `ANTIOQUIA`, etc.
- Agrupaciones especiales de Generación Distribuida (`GD_UPME`, `GD_PNUMA`)

**Nota:** Esta tabla es compartida con las otras métricas (energía eléctrica, potencia máxima).

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `serial` | **PK** |
| `codigo` | `text` | Código técnico único (ej. `SIN`, `CARIBE`, `GD_UPME`) |
| `nombre` | `text` | Nombre legible |
| `categoria` | `text` | CHECK (`'nacional'`, `'area_sin'`, `'combinado'`, `'gd'`, `'proyecto'`) |
| `descripcion` | `text` | Notas adicionales |
| `created_at` | `timestamptz` | Timestamp automático |

### 2. `fact_capacidad_instalada`

Tabla de hechos para series **anuales** de **capacidad instalada de generación distribuida** (MW):

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `bigserial` | **PK** |
| `tiempo_id` | `int` | **FK** → `dim_tiempo.id` (ya definida en el esquema global) |
| `periodicidad` | `text` | `'anual'` (solo disponible anualmente) |
| `unidad` | `text` | Unidad original (`MW-año`) |
| `area_id` | `int` | **FK** → `dim_areas_electricas.id` |
| `descriptor` | `text` | Subnivel (por ejemplo nombre de proyecto GD) |
| `escenario` | `text` | `'ESC_BAJO'`, `'ESC_MEDIO'`, `'ESC_ALTO'`, `'IC_SUP_95'`, `'IC_INF_95'`, `'IC_SUP_68'`, `'IC_INF_68'` |
| `revision` | `text` | Etiqueta de revisión (`REV_JULIO_2025`, `REV_DIC_2023`, etc.) |
| `year_span` | `text` | Rango de años publicado (`2025-2039`, `2024-2038`, ...) |
| `valor` | `numeric(18,6)` | Valor numérico de capacidad instalada en MW |
| `sheet_name` | `text` | Nombre de la hoja Excel de origen |
| `source_file` | `text` | Nombre del archivo Excel de origen |
| `source_id` | `text` | **FK** → `etl_sources.id` (para trazabilidad ETL) |
| `etl_timestamp` | `timestamptz` | Timestamp de carga |

**Constraint sugerida** (idempotencia):

- `UNIQUE(tiempo_id, area_id, descriptor, escenario, periodicidad, revision)`

Esto permite recargar la misma revisión sin duplicar registros y deja
espacio para futuras revisiones (ej. una nueva versión 2026).

**Nota importante:** A diferencia de energía y potencia, la capacidad instalada solo está disponible con periodicidad **anual**.

### Hojas Excel procesadas

El normalizador `normalizers/capacidad_instalada.py` procesa la siguiente hoja:

- **Hoja 13**: Capacidad instalada anual de Generación Distribuida (MW-año) - GD

### Relación con el normalizador

El módulo `normalizers/capacidad_instalada.py` produce registros con la siguiente forma:

- `period_key` → se resuelve a `tiempo_id` usando `dim_tiempo`
- `periodicidad` → siempre `'anual'`
- `metric` → siempre `'capacidad'`
- `unidad` → `unidad` (típicamente `MW-año`)
- `ambito` → se mapea a `dim_areas_electricas.codigo` (típicamente `'gd'`)
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
3. Insertar en `fact_capacidad_instalada` respetando la clave única de idempotencia.

### Índices

Se crean índices en:
- `tiempo_id` (para consultas temporales)
- `area_id` (para filtros por área)
- `escenario` (para filtros por escenario)
- `revision` (para filtros por revisión)
- `source_id` (para trazabilidad ETL)

### Diferencias con otras métricas

- **Periodicidad limitada**: Solo disponible anualmente (no hay datos mensuales)
- **Ámbito específico**: Principalmente relacionado con Generación Distribuida (GD)
- **Menor volumen de datos**: Solo una hoja Excel vs 6 hojas para energía y potencia

