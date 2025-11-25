from abc import ABC, abstractmethod
from typing import Dict, Any, List
from logs_config.logger import app_logger as logger

class BaseTransformer(ABC):
    """
    Clase base abstracta para transformers.
    
    Los transformers reciben datos RAW del Storage y los transforman
    a un formato normalizado y validado listo para carga en PostgreSQL.
    """
    
    @abstractmethod
    def transform(self, raw_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma datos RAW a estructura normalizada.
        
        Args:
            raw_data: Datos en formato RAW (JSON, bytes, DataFrame, etc.)
            source_config: Configuración completa de la fuente desde etl_sources
            
        Returns:
            Diccionario con estructura:
            {
                "valid_records": [
                    {
                        "fact_table": "fact_regalias",
                        "data": {...},  # Registro validado
                        "dimensions": {
                            "tiempo": {...},
                            "campo": {...},
                            "territorio": {...}
                        }
                    },
                    ...
                ],
                "errors": [
                    {
                        "record_index": 123,
                        "error": "ValidationError: ...",
                        "raw_record": {...}
                    },
                    ...
                ],
                "stats": {
                    "total_raw": 1000,
                    "valid": 995,
                    "errors": 5,
                    "processing_time_seconds": 12.5
                }
            }
            
        Raises:
            Exception: Si hay error crítico que impide el procesamiento
        """
        pass
    
    def _validate_record(self, record: Dict[str, Any], schema_class) -> Dict[str, Any]:
        """
        Valida un registro usando el modelo Pydantic correspondiente.
        
        Args:
            record: Registro a validar
            schema_class: Clase Pydantic del schema (ej: FactRegaliasSchema)
            
        Returns:
            Diccionario con registro validado
            
        Raises:
            ValidationError: Si el registro no cumple el schema
        """
        validated = schema_class(**record)
        return validated.model_dump()
