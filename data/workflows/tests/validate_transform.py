"""
Script de validación del flujo Extract → Transform para api_regalias.

Supone que el extraction ya se completó exitosamente y los datos RAW están 
en el bucket Storage (raw-data/api/api_regalias/...).

Soporta múltiples archivos (lotes con paginación):
  - Detección automática de lote por timestamp
  - Descarga de TODOS los archivos del lote más reciente
  - Transformación individual + combinación de resultados

Uso:
  python -m workflows.tests.validate_transform

Flujo (5 pasos):
  1. Obtener archivos RAW más recientes de Storage
  2. Verificar TransformationConfig
  3. Cargar ApiTransformer
  4. Transformar archivos (cada uno → combinar)
  5. Validar resultados y generar reporte

NOTA: Funciones comunes importadas desde run.py para evitar duplicación.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from services.backend_client import BackendClient
from workflows.full_etl.transformers import get_transformer, get_transformation_config
from workflows.full_etl.run import _get_latest_raw_files, _transform_multiple_files, _pct
from logs_config.logger import app_logger as logger


def main():
    """Main validation flow."""
    logger.info("="*70)
    logger.info("[VALIDACION] Iniciando validacion Extract -> Transform para api_regalias")
    logger.info("="*70)
    
    source_id = "api_regalias"
    source_config = {"id": source_id, "storage": {"bucket": "raw-data"}}
    
    # 1. Obtener archivos RAW mas recientes
    logger.info(f"\n[1/5] Buscando archivos RAW más recientes para {source_id}...")
    raw_files = _get_latest_raw_files(source_id, source_config=source_config)
    if raw_files is None:
        logger.error("No se encontró archivo RAW. Verifica que el extraction completó exitosamente.")
        return False
    
    logger.info(f"[✓] Lote encontrado: {len(raw_files)} archivo(s)")
    for file_path, _ in raw_files:
        logger.info(f"    - {file_path}")
    
    # 2. Verificar TransformationConfig
    logger.info(f"\n[2/5] Verificando TransformationConfig para {source_id}...")
    transform_config = get_transformation_config(source_id)
    if not transform_config:
        logger.error(f"No hay TransformationConfig registrada para {source_id}")
        return False
    
    logger.info(f"[✓] Configuración encontrada:")
    logger.info(f"    - Fact table: {transform_config.fact_mapping.fact_table}")
    logger.info(f"    - Validaciones: {len(transform_config.column_validations)}")
    logger.info(f"    - Derivaciones: {len(transform_config.column_derivations)}")
    logger.info(f"    - Dimensiones: {len(transform_config.fact_mapping.dimension_mappings)}")
    
    # 3. Obtener transformer
    logger.info(f"\n[3/5] Cargando ApiTransformer para {source_id}...")
    transformer = get_transformer("api")
    if not transformer:
        logger.error("No se pudo obtener ApiTransformer")
        return False
    logger.info(f"[✓] Transformer cargado")
    
    # 4. Transformar archivos
    logger.info(f"\n[4/5] Transformando {len(raw_files)} archivo(s)...")
    try:
        result = _transform_multiple_files(raw_files, transformer, source_config)
    except Exception as e:
        logger.error(f"Error durante transformación: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Validar resultados
    logger.info(f"\n[5/5] Validando resultados...")
    
    stats = result.get("stats", {})
    valid_records = result.get("valid_records", [])
    errors = result.get("errors", [])
    
    logger.info(f"[✓] Transformación completada:")
    logger.info(f"    - Archivos procesados: {stats.get('files_processed')}")
    logger.info(f"    - Total RAW: {stats.get('total_raw')}")
    logger.info(f"    - Válidos: {stats.get('valid')} ({_pct(stats.get('valid'), stats.get('total_raw'))}%)")
    logger.info(f"    - Errores: {stats.get('errors')} ({_pct(stats.get('errors'), stats.get('total_raw'))}%)")
    logger.info(f"    - Tiempo total: {stats.get('processing_time_seconds', 0):.2f}s")
    
    # Mostrar categorias de error
    error_categories = stats.get("error_categories", {})
    if error_categories:
        logger.info(f"\n    Categorías de error (combinadas):")
        for category, count in sorted(error_categories.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"      - {category}: {count}")
    
    # Validar estructura de registros validos
    if valid_records:
        logger.info(f"\nEstructura de registros válidos:")
        sample_record = valid_records[0]
        logger.info(f"    - fact_table: {sample_record.get('fact_table')}")
        logger.info(f"    - data keys: {list(sample_record.get('data', {}).keys())[:5]}...")
        logger.info(f"    - dimensions: {list(sample_record.get('dimensions', {}).keys())}")
    
    # Mostrar sample de errores si hay
    if errors:
        logger.info(f"\nSample de errores (primeros 3):")
        for i, error in enumerate(errors[:3], 1):
            logger.info(f"    [{i}] Archivo: {error.get('file', 'unknown')}, Registro #{error.get('record_index')}: {error.get('error')}")
    
    # Resumen final
    success_rate = stats.get('valid') / max(stats.get('total_raw'), 1) * 100
    logger.info(f"\n{'='*70}")
    if success_rate >= 95:
        logger.info(f"VALIDACIÓN EXITOSA - Tasa de éxito: {success_rate:.1f}%")
        logger.info(f"Todos los {len(raw_files)} archivo(s) procesados correctamente.")
    elif success_rate >= 80:
        logger.info(f"VALIDACIÓN PARCIAL - Tasa de éxito: {success_rate:.1f}% (revisar errores)")
    else:
        logger.error(f"VALIDACIÓN FALLIDA - Tasa de éxito: {success_rate:.1f}%")
        return False
    
    logger.info(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
