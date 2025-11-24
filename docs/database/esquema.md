# Esquema de Base de Datos

Este documento detalla la estructura de la base de datos en Supabase (PostgreSQL) utilizada para orquestar el ETL.

## Diagrama Relacional Simplificado

`etl_sources (1) <---> (N) source_check_history`

## Tablas

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

## Tipos Enumerados (ENUMs)

*   **`source_update_method`**: `'api'`, `'scraping'`, `'html'`, `'archivo'`, `'complex_scraper'`
*   **`source_check_status`**: `'no_change'`, `'changed'`, `'failed'`

## Migracion script

El script .sql para crear la base de datos se encuentra en: [script migración](https://github.com/Ashen-Software/Suria/blob/data/docs/database/init_db.sql).
