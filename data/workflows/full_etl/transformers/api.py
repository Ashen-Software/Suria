"""
Transformer para datos de APIs (principalmente Socrata).

Parsea JSON descargado por ApiExtractor y lo transforma a estructura
normalizada validada con schemas Pydantic.
"""
import json
import time
from typing import Dict, Any, List
from datetime import datetime
from .base import BaseTransformer
from .schemas import SocrataApiRegaliasRawSchema, FactRegaliasSchema
from logs_config.logger import app_logger as logger
from pydantic import ValidationError


class ApiTransformer(BaseTransformer):
    """
    Transforma datos de APIs (JSON) a estructura normalizada.
    
    Soporta:
    - API Socrata ANH (fact_regalias)
    - Otros endpoints JSON con estructura similar
    """
    
    def transform(self, raw_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma JSON de API a registros validados.
        
        Args:
            raw_data: String JSON o diccionario con respuesta de API
            source_config: Configuración de la fuente
            
        Returns:
            Diccionario con valid_records, errors y stats
        """
        start_time = time.time()
        source_id = source_config.get("id")
        
        logger.info(f"[ApiTransformer] Iniciando transformación para {source_id}")
        
        # Parsear JSON si viene como string
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError as e:
                logger.error(f"[ApiTransformer] Error parseando JSON: {e}")
                return {
                    "valid_records": [],
                    "errors": [{"record_index": 0, "error": str(e), "raw_record": None}],
                    "stats": {
                        "total_raw": 0,
                        "valid": 0,
                        "errors": 1,
                        "processing_time_seconds": time.time() - start_time
                    }
                }
        
        # Detectar tipo de fuente para aplicar schema correcto
        transformer_fn = self._get_transformer_function(source_id)
        
        # Extraer array de datos (estructura de Socrata: {"data": [...]} o directo [...])
        if isinstance(raw_data, dict) and "data" in raw_data:
            records = raw_data["data"]
        elif isinstance(raw_data, list):
            records = raw_data
        else:
            logger.error(f"[ApiTransformer] Estructura JSON no reconocida: {type(raw_data)}")
            return {
                "valid_records": [],
                "errors": [{"record_index": 0, "error": "Estructura JSON inválida", "raw_record": raw_data}],
                "stats": {
                    "total_raw": 0,
                    "valid": 0,
                    "errors": 1,
                    "processing_time_seconds": time.time() - start_time
                }
            }
        
        # Procesar cada registro
        valid_records = []
        errors = []
        
        for idx, raw_record in enumerate(records):
            try:
                validated_record = transformer_fn(raw_record, source_id)
                valid_records.append(validated_record)
            except ValidationError as e:
                logger.warning(f"[ApiTransformer] Error validación registro {idx}: {e}")
                errors.append({
                    "record_index": idx,
                    "error": str(e),
                    "raw_record": raw_record
                })
            except Exception as e:
                logger.error(f"[ApiTransformer] Error inesperado registro {idx}: {e}")
                errors.append({
                    "record_index": idx,
                    "error": f"Error inesperado: {str(e)}",
                    "raw_record": raw_record
                })
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"[ApiTransformer] Transformación completada para {source_id}: "
            f"{len(valid_records)} válidos, {len(errors)} errores en {processing_time:.2f}s"
        )
        
        return {
            "valid_records": valid_records,
            "errors": errors,
            "stats": {
                "total_raw": len(records),
                "valid": len(valid_records),
                "errors": len(errors),
                "processing_time_seconds": processing_time
            }
        }
    
    def _get_transformer_function(self, source_id: str):
        """
        Retorna la función de transformación apropiada según el source_id.
        
        Args:
            source_id: Identificador de la fuente
            
        Returns:
            Función que transforma raw_record → validated_record
        """
        # Mapeo de source_id a función de transformación
        transformers = {
            "api_regalias": self._transform_socrata_regalias,
            # Agregar demas fuentes
        }
        
        return transformers.get(source_id, self._transform_generic_json)
    
    def _transform_socrata_regalias(self, raw_record: Dict[str, Any], source_id: str) -> Dict[str, Any]:
        """
        Transforma registro de API Socrata ANH (regalías) a estructura normalizada.
        
        Args:
            raw_record: Registro RAW del JSON
            source_id: ID de la fuente
            
        Returns:
            Diccionario con estructura lista para Loader
        """
        # Validar con schema RAW de Socrata
        socrata_schema = SocrataApiRegaliasRawSchema(**raw_record)
        
        # Convertir a schema de fact_regalias
        fact_regalias = socrata_schema.to_fact_regalias(source_id)
        
        # Retornar estructura para el Loader
        return {
            "fact_table": "fact_regalias",
            "data": fact_regalias.model_dump(),
            "dimensions": {
                "tiempo": {
                    "fecha": fact_regalias.tiempo_fecha,
                    "anio": fact_regalias.tiempo_fecha.year,
                    "mes": fact_regalias.tiempo_fecha.month,
                    "es_proyeccion": False
                },
                "territorio": {
                    "departamento": fact_regalias.departamento,
                    "municipio": fact_regalias.municipio,
                    "latitud": fact_regalias.latitud,
                    "longitud": fact_regalias.longitud
                },
                "campo": {
                    "nombre_campo": fact_regalias.campo_nombre,
                    "contrato": fact_regalias.contrato,
                    "activo": True
                }
            }
        }
    
    def _transform_generic_json(self, raw_record: Dict[str, Any], source_id: str) -> Dict[str, Any]:
        """
        Transformación genérica para JSONs que no tienen schema específico.
        Solo pasa los datos sin validación estricta.
        
        Args:
            raw_record: Registro RAW del JSON
            source_id: ID de la fuente
            
        Returns:
            Diccionario con datos RAW
        """
        logger.warning(
            f"[ApiTransformer] Usando transformación genérica para {source_id}. "
            "Considere implementar schema específico."
        )
        
        return {
            "fact_table": "unknown",
            "data": raw_record,
            "dimensions": {}
        }
