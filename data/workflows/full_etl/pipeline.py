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


def transform_excel_batch(
    metadata: Dict[str, Any],
    excel_files: Dict[str, bytes],
    source_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Orquesta la transformación de un lote de archivos Excel.
    
    Usa el registry de source_transformers para obtener el transformer
    específico de la fuente, o usa ExcelTransformer genérico como fallback.
    
    Args:
        metadata: Contenido parseado del metadata.json
        excel_files: Dict {filename: bytes} de archivos Excel
        source_config: Configuración de la fuente
        
    Returns:
        Dict con valid_records, errors, stats (y resoluciones si aplica)
    """
    from workflows.full_etl.transformers import get_transformer_for_source
    from workflows.full_etl.transformers.excel import ExcelTransformer
    
    start_time = time.time()
    source_id = source_config.get("id")
    
    logger.info(
        f"[pipeline] Iniciando transformación batch Excel: "
        f"{len(excel_files)} archivos para {source_id}"
    )
    
    # Obtener transformer apropiado (especifico o generico)
    transformer = get_transformer_for_source(source_config)
    
    # Si tiene metodo transform_batch, usarlo
    if hasattr(transformer, 'transform_batch'):
        result = transformer.transform_batch(excel_files, metadata, source_config)
    else:
        # Fallback a ExcelTransformer generico
        excel_transformer = ExcelTransformer()
        result = excel_transformer.transform_batch(excel_files, metadata, source_config)
    
    # Agregar info de metadata a stats
    result["stats"]["extraction_date"] = metadata.get("extraction_date")
    result["stats"]["source_url"] = metadata.get("source_url")
    result["stats"]["total_declarations"] = metadata.get("total_declarations", 0)
    
    processing_time = time.time() - start_time
    result["stats"]["total_processing_time"] = processing_time
    
    logger.info(
        f"[pipeline] Transformación batch completada: "
        f"{result['stats']['valid']} registros válidos, "
        f"{result['stats']['errors']} errores"
    )
    
    return result


# Alias para compatibilidad con codigo existente
def transform_minminas_excel_batch(
    metadata: Dict[str, Any],
    excel_files: Dict[str, bytes],
    source_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Alias para compatibilidad. Usa transform_excel_batch internamente.
    
    @deprecated: Usar transform_excel_batch() en su lugar.
    """
    logger.warning(
        "[pipeline] transform_minminas_excel_batch está deprecado. "
        "Usar transform_excel_batch() en su lugar."
    )
    return transform_excel_batch(metadata, excel_files, source_config)


def success_percentage(valid: int, total: int) -> float:
    """Calcula porcentaje de exito."""
    if total == 0:
        return 0.0
    return (valid / total) * 100
