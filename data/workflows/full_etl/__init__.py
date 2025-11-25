# Full ETL workflow

"""
Estructura modular:

run.py
  - Orquestador principal (full_etl_task)
  - Despacha a extractores, transformadores, loaders

storage.py
  - get_latest_raw_files(): Descarga archivos del bucket Storage
  - Manejo de lotes por timestamp
  - Validación básica de JSON

pipeline.py
  - transform_multiple_files(): Transforma lotes de archivos
  - success_percentage(): Calcula tasa de éxito
  - Combina resultados (válidos, errores, stats)

transformers/
  - ApiTransformer: Genérico para APIs (ej: Socrata)
  - config.py: Configuraciones parametrizadas por fuente
  - schemas.py: Validación con Pydantic

extractors/
  - WebExtractor, ApiExtractor, etc.

loaders/ (TODO)
  - PostgreSQL loader
"""