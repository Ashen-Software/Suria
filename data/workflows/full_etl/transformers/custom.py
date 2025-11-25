"""
Transformer para scripts de transformación personalizados (complex_scraper).

Ejecuta funciones de transformación definidas en scripts custom
siguiendo la convención de extraction/scrapers/scraper_loader.py
"""
import importlib
import time
from typing import Dict, Any, List
from .base import BaseTransformer
from logs_config.logger import app_logger as logger


class CustomTransformer(BaseTransformer):
    """
    Ejecuta scripts de transformación personalizados.
    
    Convención:
    - El script debe estar en: data/workflows/full_etl/transformers/custom_scripts/
    - Nombre del archivo: {source_id}_transformer.py o config.script_name
    - Debe exponer función: transform(raw_data, source_config) -> dict
    - El dict retornado debe tener estructura:
      {
          "valid_records": [...],
          "errors": [...],
          "stats": {...}
      }
    """
    
    def transform(self, raw_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta script custom de transformación.
        
        Args:
            raw_data: Datos RAW (puede ser bytes, string, dict, etc.)
            source_config: Configuración de la fuente
            
        Returns:
            Diccionario con valid_records, errors y stats
        """
        start_time = time.time()
        source_id = source_config.get("id")
        config = source_config.get("config", {})
        
        # Permitir override del nombre del script en config, o usar el ID por defecto
        script_name = config.get("transform_script_name", f"{source_id}_transformer")
        
        try:
            # Importar: workflows.full_etl.transformers.custom_scripts.<script_name>
            module_path = f"workflows.full_etl.transformers.custom_scripts.{script_name}"
            logger.info(f"[CustomTransformer] Cargando módulo: {module_path}")
            
            module = importlib.import_module(module_path)
            
            if not hasattr(module, 'transform'):
                raise AttributeError(
                    f"El módulo {script_name} no tiene función 'transform(raw_data, source_config)'"
                )
            
            # Ejecutar funcion de transformacion
            transform_func = getattr(module, 'transform')
            result = transform_func(raw_data, source_config)
            
            # Validar estructura del resultado
            if not isinstance(result, dict):
                raise ValueError(
                    f"La función transform() debe retornar dict, se obtuvo {type(result)}"
                )
            
            required_keys = {"valid_records", "errors", "stats"}
            if not required_keys.issubset(result.keys()):
                raise ValueError(
                    f"El dict retornado debe contener: {required_keys}, "
                    f"se encontró: {result.keys()}"
                )
            
            # Agregar tiempo de procesamiento total si no está incluido
            if "processing_time_seconds" not in result["stats"]:
                result["stats"]["processing_time_seconds"] = time.time() - start_time
            
            logger.info(
                f"[CustomTransformer] Script {script_name} ejecutado: "
                f"{result['stats'].get('valid', 0)} válidos, "
                f"{result['stats'].get('errors', 0)} errores"
            )
            
            return result
            
        except ImportError as e:
            logger.error(
                f"[CustomTransformer] No se encontró el script {script_name}.py en "
                f"data/workflows/full_etl/transformers/custom_scripts/"
            )
            return {
                "valid_records": [],
                "errors": [{
                    "record_index": 0,
                    "error": f"Script no encontrado: {str(e)}",
                    "raw_record": None
                }],
                "stats": {
                    "total_raw": 0,
                    "valid": 0,
                    "errors": 1,
                    "processing_time_seconds": time.time() - start_time
                }
            }
        except Exception as e:
            logger.exception(f"[CustomTransformer] Error ejecutando script {script_name}: {e}")
            return {
                "valid_records": [],
                "errors": [{
                    "record_index": 0,
                    "error": str(e),
                    "raw_record": None
                }],
                "stats": {
                    "total_raw": 0,
                    "valid": 0,
                    "errors": 1,
                    "processing_time_seconds": time.time() - start_time
                }
            }
