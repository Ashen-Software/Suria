"""
Ejemplo de script custom de transformación.

Este archivo muestra la estructura que deben seguir los scripts
de transformación personalizados.

Para crear un nuevo transformer custom:
1. Copiar este archivo con nombre: {source_id}_transformer.py
2. Implementar la función transform(raw_data, source_config)
3. Retornar dict con estructura: {valid_records, errors, stats}
"""
from typing import Dict, Any
from logs_config.logger import app_logger as logger


def transform(raw_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función de transformación custom.
    
    Args:
        raw_data: Datos RAW (bytes, string, dict, etc.)
        source_config: Configuración completa de la fuente
        
    Returns:
        dict con estructura:
        {
            "valid_records": [
                {
                    "fact_table": "nombre_tabla",
                    "data": {...},
                    "dimensions": {...}
                },
                ...
            ],
            "errors": [
                {
                    "record_index": int,
                    "error": str,
                    "raw_record": dict
                },
                ...
            ],
            "stats": {
                "total_raw": int,
                "valid": int,
                "errors": int,
                "processing_time_seconds": float (opcional)
            }
        }
    """
    source_id = source_config.get("id")
    logger.info(f"[CustomScript] Transformando {source_id}")
    
    valid_records = []
    errors = []
    
    # TODO: Logica de transformacion real
    # Ejemplo:
    try:
        # Parsear raw_data
        # Validar datos
        # Construir registros normalizados
        
        # Ejemplo de registro válido:
        valid_records.append({
            "fact_table": "fact_example",
            "data": {
                "campo1": "valor1",
                "campo2": 123
            },
            "dimensions": {
                "tiempo": {
                    "fecha": "2024-01-01",
                    "anio": 2024,
                    "mes": 1
                }
            }
        })
        
    except Exception as e:
        logger.error(f"[CustomScript] Error: {e}")
        errors.append({
            "record_index": 0,
            "error": str(e),
            "raw_record": raw_data
        })
    
    return {
        "valid_records": valid_records,
        "errors": errors,
        "stats": {
            "total_raw": len(valid_records) + len(errors),
            "valid": len(valid_records),
            "errors": len(errors)
        }
    }
