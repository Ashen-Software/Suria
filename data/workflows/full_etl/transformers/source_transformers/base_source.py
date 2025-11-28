"""
Clase base para transformers específicos de fuente.

Los source transformers encapsulan toda la lógica particular de una fuente
de datos, separándola de los transformers genéricos por tipo (Excel, API, etc.)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Tuple
from datetime import date
from decimal import Decimal
from pydantic import ValidationError
from logs_config.logger import app_logger as logger


# Registry global de transformers por source_id
source_transformer_registry: Dict[str, Type["BaseSourceTransformer"]] = {}


def register_source_transformer(*source_ids: str):
    """
    Decorador para registrar un transformer para uno o más source_ids.
    
    Uso:
        @register_source_transformer("minminas_oferta", "gas_natural_declaracion")
        class MinMinasTransformer(BaseSourceTransformer):
            ...
    """
    def decorator(cls: Type["BaseSourceTransformer"]):
        for source_id in source_ids:
            source_transformer_registry[source_id] = cls
            logger.debug(f"[Registry] Registrado transformer {cls.__name__} para source_id: {source_id}")
        return cls
    return decorator


def get_source_transformer(source_id: str) -> Optional["BaseSourceTransformer"]:
    """
    Obtiene una instancia del transformer para un source_id específico.
    
    Args:
        source_id: Identificador de la fuente
        
    Returns:
        Instancia del transformer o None si no existe uno específico
    """
    transformer_class = source_transformer_registry.get(source_id)
    if transformer_class:
        return transformer_class()
    return None


class BaseSourceTransformer(ABC):
    """
    Clase base abstracta para transformers específicos de fuente.
    
    Diferencia con BaseTransformer:
    - BaseTransformer: genérico por TIPO (Excel, API, Web)
    - BaseSourceTransformer: específico por FUENTE (MinMinas, UPME, etc.)
    
    Un source transformer puede:
    - Manejar archivos individuales o lotes
    - Tener métodos auxiliares específicos
    - Definir validaciones particulares
    """
    
    # IDs de fuente que maneja este transformer (para registro automático)
    source_ids: List[str] = []
    
    # Tipo de archivo que procesa (para routing en ExcelTransformer/ApiTransformer)
    file_type: str = "unknown"  # "excel", "json", "csv", etc.
    
    @abstractmethod
    def transform(self, raw_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma datos RAW a estructura normalizada.
        
        Args:
            raw_data: Datos en formato RAW
            source_config: Configuración de la fuente
            
        Returns:
            Dict con valid_records, errors, stats
        """
        pass
    
    def transform_batch(
        self, 
        files: Dict[str, Any], 
        metadata: Dict[str, Any],
        source_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transforma un lote de archivos.
        
        Por defecto procesa cada archivo individualmente.
        Override para lógica de lote personalizada.
        
        Args:
            files: Dict {filename: content}
            metadata: Metadata adicional del lote
            source_config: Configuración de la fuente
            
        Returns:
            Dict combinado con valid_records, errors, stats
        """
        all_records = []
        all_errors = []
        
        for filename, content in files.items():
            result = self.transform(content, source_config)
            all_records.extend(result.get("valid_records", []))
            all_errors.extend(result.get("errors", []))
        
        return {
            "valid_records": all_records,
            "errors": all_errors,
            "stats": {
                "total_files": len(files),
                "valid": len(all_records),
                "errors": len(all_errors)
            }
        }
    
    def _create_result(
        self,
        valid_records: List[Dict],
        errors: List[Dict],
        processing_time: float,
        **extra_stats
    ) -> Dict[str, Any]:
        """
        Crea el diccionario de resultado estándar.
        
        Args:
            valid_records: Lista de registros válidos
            errors: Lista de errores
            processing_time: Tiempo de procesamiento en segundos
            **extra_stats: Stats adicionales
            
        Returns:
            Dict con estructura estándar de resultado
        """
        stats = {
            "total_raw": len(valid_records) + len(errors),
            "valid": len(valid_records),
            "errors": len(errors),
            "processing_time_seconds": processing_time,
            **extra_stats
        }
        
        return {
            "valid_records": valid_records,
            "errors": errors,
            "stats": stats
        }
    
    def _add_error(
        self,
        errors: List[Dict],
        error: Exception,
        record_index: int = 0,
        raw_record: Any = None,
        **extra_info
    ) -> None:
        """
        Añade un error a la lista de errores con formato estándar.
        """
        errors.append({
            "record_index": record_index,
            "error": str(error),
            "raw_record": raw_record,
            **extra_info
        })
