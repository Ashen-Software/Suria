"""
Orquestación de transformación de múltiples archivos.

Responsable de:
- Transformar lotes de archivos
- Combinar resultados (registros válidos, errores, estadísticas)
- Cálculos de tasa de éxito
"""
import time
from typing import List, Dict, Tuple, Any, Optional
from logs_config.logger import app_logger as logger


def transform_multiple_files(raw_files: List[Tuple[str, str]], transformer: Any, source_config: Dict) -> Dict:
    """
    Transforma múltiples archivos RAW y combina resultados.
    
    IMPORTANTE:
    - Los archivos ya están EN MEMORIA (content_str, no path a disco)
    - Transforma cada uno individualmente
    - Combina: válidos[], errores[], stats (suma + merge)
    
    Args:
        raw_files: List de tuplas (file_path, content_str)
        transformer: Instancia del transformer (ej: ApiTransformer)
        source_config: Config de la fuente
        
    Returns:
        Dict combinado: {valid_records, errors, stats}
    """
    combined_result = {
        "valid_records": [],
        "errors": [],
        "stats": {
            "total_raw": 0,
            "valid": 0,
            "errors": 0,
            "processing_time_seconds": 0,
            "error_categories": {},
            "files_processed": len(raw_files)
        }
    }
    
    start_time = time.time()
    
    for file_idx, (file_path, raw_data) in enumerate(raw_files, 1):
        logger.info(f"[pipeline] [{file_idx}/{len(raw_files)}] Transformando: {file_path}")
        
        try:
            # Validar que raw_data no esta vacío
            if not raw_data or len(raw_data.strip()) == 0:
                logger.warning(f"[pipeline] Archivo vacío: {file_path}")
                continue
            
            # Ejecutar transformacion
            result = transformer.transform(raw_data, source_config)
            
            if result is None:
                logger.error(f"[pipeline] Transformer retornó None para {file_path}")
                continue
            
            # Agregar resultados
            valid_recs = result.get("valid_records", [])
            errors = result.get("errors", [])
            stats = result.get("stats", {})
            
            logger.debug(f"[pipeline]   -> Validos: {len(valid_recs)}, Errores: {len(errors)}, Total RAW: {stats.get('total_raw', 0)}")
            
            combined_result["valid_records"].extend(valid_recs)
            combined_result["errors"].extend(errors)
            
            # Actualizar stats
            combined_result["stats"]["total_raw"] += stats.get("total_raw", 0)
            combined_result["stats"]["valid"] += stats.get("valid", 0)
            combined_result["stats"]["errors"] += stats.get("errors", 0)
            
            # Mergear error categories
            for category, count in stats.get("error_categories", {}).items():
                combined_result["stats"]["error_categories"][category] = \
                    combined_result["stats"]["error_categories"].get(category, 0) + count
                    
        except Exception as e:
            logger.error(f"[pipeline] Error transformando {file_path}: {e}")
            import traceback
            traceback.print_exc()
            # Continuar con siguientes archivos
    
    combined_result["stats"]["processing_time_seconds"] = time.time() - start_time
    
    logger.info(f"[pipeline] Transformacion completa: {combined_result['stats']['files_processed']} archivo(s), "
                f"{combined_result['stats']['total_raw']} registros totales")
    
    return combined_result


def success_percentage(valid: int, total: int) -> float:
    """Calcula porcentaje de exito."""
    if total == 0:
        return 0.0
    return (valid / total) * 100
