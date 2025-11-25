## Plan: Arquitectura de Transformación y Carga (Transform & Load)

El pipeline ETL actualmente solo implementa la fase de **Extracción** a Supabase Storage. Este plan define la arquitectura para agregar las fases de **Transformación** (normalización, validación, parsing) y **Carga** (inserción a PostgreSQL) que completarán el flujo de datos hacia las tablas analíticas.

### Pasos

1. **Crear módulo `data/workflows/full_etl/transformers/` con arquitectura espejo a `extractors/`**
   - Implementar `base.py` con clase abstracta `BaseTransformer` que expone método `transform(raw_data, source_config) → dict`
   - Crear `api.py` (parsea JSON de APIs Socrata), `excel.py` (parsea archivos UPME/MinMinas con openpyxl/pandas), `custom.py` (ejecuta scripts personalizados)
   - Registry en `__init__.py` que mapea `source.type` → Transformer correspondiente
   - Integrar validación de schemas con Pydantic models (uno por cada fact table)

2. **Crear módulo `data/workflows/full_etl/loaders/` para gestionar escritura a PostgreSQL**
   - Implementar `dimension_loader.py` con lookups inteligentes para `dim_tiempo`, `dim_campos`, `dim_territorios` (pattern: buscar existente o insertar nuevo y devolver FK)
   - Crear `fact_loader.py` con UPSERTs basados en unique constraints (`tiempo_id` + `campo_id` + `source_id`) para idempotencia
   - Extender `data/services/backend_client.py` agregando método `get_db_connection()` que retorne cursor PostgreSQL vía `psycopg2`
   - Manejar transacciones: rollback completo si falla cualquier batch, con logging detallado de errores

3. **Modificar `data/workflows/full_etl/run.py` para orquestar Transform → Load después de Extract**
   - Después de `extractor.extract()`, listar archivos generados en Storage con filtro por timestamp
   - Para cada archivo RAW: instanciar Transformer → parsear → validar con Pydantic → pasar a Loader
   - Implementar batch processing (chunks de 5000 registros) para evitar memory overflow en datasets grandes
   - Actualizar `source_check_history.metadata` con estadísticas: registros procesados, errores, duración

4. **Crear scripts de inicialización en `data/workflows/seed/` para poblar dimensiones base**
   - `seed_dim_tiempo.py`: generar registros mensuales 2010-2036 con campos derivados (trimestre, semestre)
   - `seed_dim_territorios.py`: importar CSV del DANE con códigos DIVIPOLA + coordenadas

5. **Implementar tracking de archivos procesados para evitar re-procesamiento**
   - Crear tabla `etl_processed_files` en Supabase con columnas: `source_id`, `file_path`, `processed_at`, `records_count`, `status`
   - En `run.py`: antes de transformar, verificar si `file_path` ya existe en tabla; si sí, skip
   - Insertar registro al finalizar Load exitoso, con hash SHA256 del archivo para detectar cambios

### Consideraciones Adicionales

2. **Gestión de errores parciales** — Dead letter queue en Storage (recomendado para producción)
3. **Validación de integridad de FKs antes de INSERT** — Sí, verificar que todas las dimensiones referenciadas existan antes de insertar facts, con fallback a crear registros dummy temporales marcados como `needs_review: true`
