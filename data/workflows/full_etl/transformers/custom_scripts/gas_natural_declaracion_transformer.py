"""
Transformer custom para Declaraciones de Producción de Gas Natural.

Transforma el JSON extraído por el scraper a registros normalizados
para insertar en la base de datos de declaraciones.

Estructura de entrada (JSON del scraper):
{
    "extraction_date": "...",
    "source_url": "...",
    "declarations": [
        {
            "declaration_title": "Declaración de Producción de Gas Natural 2025 - 2034",
            "resolutions": [
                {
                    "number": "00739",
                    "date": "2025-05-28",
                    "url": "...",
                    "title": "...",
                    "soporte_magnetico": [...]
                }
            ],
            "cronograma": {...},
            "anexos": [...],
            "acceso_sistema": {...}
        }
    ],
    "plantillas": [...]
}

Salida esperada por CustomTransformer:
{
    "valid_records": [...],
    "errors": [...],
    "stats": {...}
}
"""
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from logs_config.logger import app_logger as logger


def transform(raw_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforma el JSON de declaraciones de gas natural a registros normalizados.
    
    Args:
        raw_data: Datos RAW (string JSON o bytes)
        source_config: Configuración de la fuente
        
    Returns:
        Dict con valid_records, errors y stats
    """
    start_time = time.time()
    source_id = source_config.get("id", "gas_natural_declaracion")
    
    logger.info(f"[{source_id}_transformer] Iniciando transformación")
    
    valid_records: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    stats = {
        "total_raw": 0,
        "valid": 0,
        "errors": 0,
        "declarations_processed": 0,
        "resolutions_processed": 0,
        "error_categories": {}
    }
    
    try:
        # Parsear JSON si viene como string o bytes
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode('utf-8')
        if isinstance(raw_data, str):
            data = json.loads(raw_data)
        else:
            data = raw_data
        
        extraction_date = data.get("extraction_date")
        source_url = data.get("source_url")
        declarations = data.get("declarations", [])
        plantillas = data.get("plantillas", [])
        
        logger.info(
            f"[{source_id}_transformer] Datos cargados: "
            f"{len(declarations)} declaraciones, {len(plantillas)} plantillas"
        )
        
        # Procesar cada declaración
        for decl_idx, declaration in enumerate(declarations):
            declaration_title = declaration.get("declaration_title", "Unknown")
            resolutions = declaration.get("resolutions", [])
            cronograma = declaration.get("cronograma")
            anexos = declaration.get("anexos", [])
            acceso_sistema = declaration.get("acceso_sistema")
            
            stats["declarations_processed"] += 1
            
            # Crear registro de declaración
            declaration_record = {
                "fact_table": "declarations",
                "data": {
                    "declaration_title": declaration_title,
                    "total_resolutions": len(resolutions),
                    "extraction_date": extraction_date,
                    "source_url": source_url,
                },
                "dimensions": {},
                "nested_records": {
                    "resolutions": [],
                    "cronograma": cronograma,
                    "anexos": anexos,
                    "acceso_sistema": acceso_sistema
                }
            }
            
            # Procesar resoluciones de esta declaración
            for res_idx, resolution in enumerate(resolutions):
                stats["total_raw"] += 1
                stats["resolutions_processed"] += 1
                
                try:
                    res_record = _transform_resolution(resolution, declaration_title)
                    declaration_record["nested_records"]["resolutions"].append(res_record)
                    
                except Exception as e:
                    error_msg = str(e)
                    error_category = _categorize_error(error_msg)
                    
                    errors.append({
                        "record_index": res_idx,
                        "declaration": declaration_title,
                        "resolution": resolution.get("number", "unknown"),
                        "error": error_msg,
                        "category": error_category,
                        "raw_record": resolution
                    })
                    stats["error_categories"][error_category] = \
                        stats["error_categories"].get(error_category, 0) + 1
            
            valid_records.append(declaration_record)
        
        # Procesar plantillas (si existen)
        for plantilla in plantillas:
            plantilla_record = {
                "fact_table": "plantillas_declaracion",
                "data": {
                    "type": plantilla.get("type"),
                    "declaration_title": plantilla.get("declaration_title"),
                    "extraction_date": extraction_date,
                },
                "dimensions": {},
                "nested_records": {
                    "plantillas": plantilla.get("plantillas", [])
                }
            }
            valid_records.append(plantilla_record)
        
        stats["valid"] = len(valid_records)
        stats["errors"] = len(errors)
        stats["processing_time_seconds"] = time.time() - start_time
        
        logger.info(
            f"[{source_id}_transformer] Transformación completada: "
            f"{stats['valid']} registros válidos, {stats['errors']} errores"
        )
        
        return {
            "valid_records": valid_records,
            "errors": errors,
            "stats": stats
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"[{source_id}_transformer] Error parseando JSON: {e}")
        return {
            "valid_records": [],
            "errors": [{"error": f"JSON parse error: {e}", "raw_record": None}],
            "stats": {
                **stats,
                "errors": 1,
                "processing_time_seconds": time.time() - start_time
            }
        }
    except Exception as e:
        logger.error(f"[{source_id}_transformer] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return {
            "valid_records": [],
            "errors": [{"error": str(e), "raw_record": None}],
            "stats": {
                **stats,
                "errors": 1,
                "processing_time_seconds": time.time() - start_time
            }
        }


def _transform_resolution(resolution: Dict[str, Any], declaration_title: str) -> Dict[str, Any]:
    """
    Transforma una resolución individual.
    
    Args:
        resolution: Diccionario con datos de la resolución
        declaration_title: Título de la declaración padre
        
    Returns:
        Dict con datos normalizados de la resolución
    """
    # Parsear fecha si existe
    date_str = resolution.get("date")
    parsed_date = None
    if date_str:
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
        except ValueError:
            parsed_date = date_str  # Mantener original si no se puede parsear
    
    # Procesar soportes magnéticos
    soportes = resolution.get("soporte_magnetico", [])
    processed_soportes = []
    
    if soportes:
        for soporte in soportes:
            processed_soportes.append({
                "title": soporte.get("title"),
                "url": soporte.get("url"),
                "local_path": soporte.get("local_path"),
                "file_size_bytes": soporte.get("file_size_bytes"),
                "file_size_mb": soporte.get("file_size_mb"),
            })
    
    return {
        "number": resolution.get("number"),
        "date": parsed_date,
        "url": resolution.get("url"),
        "title": resolution.get("title"),
        "declaration_title": declaration_title,
        "soporte_magnetico": processed_soportes,
        "extracted_data": resolution.get("extracted_data")
    }


def _categorize_error(error_msg: str) -> str:
    """
    Categoriza un error para métricas.
    
    Args:
        error_msg: Mensaje de error
        
    Returns:
        Categoría del error
    """
    error_lower = error_msg.lower()
    
    if "date" in error_lower or "fecha" in error_lower:
        return "date_format"
    elif "url" in error_lower:
        return "invalid_url"
    elif "required" in error_lower or "null" in error_lower:
        return "missing_field"
    elif "type" in error_lower or "conversion" in error_lower:
        return "type_conversion"
    else:
        return "other"
