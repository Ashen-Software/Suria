"""
Transformer optimizado y genérico para datos de APIs (principalmente Socrata).

Optimizaciones aplicadas:
 - Deserialización rápida con orjson (si disponible) o json.
 - Uso de pandas para operaciones vectorizadas (filtrado y derivación de columnas).
 - Pre-validaciones masivas antes de invocar Pydantic por registro.
 - Categorización de errores por tipo para métricas más ricas.
 - Sistema de configuración parametrizado: reutilizable para cualquier API Socrata.
 - Mantiene contrato de salida (valid_records, errors, stats) para compatibilidad.

Flujo general (dirigido por TransformationConfig):
  1. Parsear JSON rápido
  2. Extraer lista de registros
  3. Cargar en DataFrame
  4. Aplicar validaciones pre-Pydantic vectorizadas
  5. Derivar columnas (fecha, cálculos, etc.)
  6. Mapear a fact table + dimensiones
  7. Validar con Pydantic (solo filas limpias)
"""
import time
import json
from typing import Dict, Any, Optional
from .base import BaseTransformer
from .config import get_transformation_config, ValidationRule
from .data_cleaner import DataValidator
from .schemas import SocrataApiRegaliasRawSchema
from logs_config.logger import app_logger as logger
from pydantic import ValidationError

# Deserializacion rapida
try:
    import orjson as _orjson
    def _fast_json_loads(data: str):
        return _orjson.loads(data)
except ImportError:
    import json as _json
    def _fast_json_loads(data: str):
        return _json.loads(data)

import pandas as pd
import numpy as np


def _sanitize_value(value):
    """
    Sanitiza un valor para evitar NaN/Inf en la salida.
    
    pandas/numpy NaN e Inf no son serializables a JSON y PostgreSQL no los acepta.
    """
    if value is None:
        return None
    if isinstance(value, float):
        if pd.isna(value) or np.isinf(value):
            return None
    # Para numpy types
    if hasattr(value, 'item'):  # numpy scalar
        try:
            py_value = value.item()
            if isinstance(py_value, float) and (pd.isna(py_value) or np.isinf(py_value)):
                return None
            return py_value
        except (ValueError, AttributeError):
            pass
    return value


def _sanitize_dict(d: dict) -> dict:
    """Sanitiza todos los valores de un diccionario."""
    return {k: _sanitize_value(v) for k, v in d.items()}


class ApiTransformer(BaseTransformer):
    """
    Transforma datos de APIs (JSON) a estructura normalizada.
    
    Genérico y reutilizable: dirigido por TransformationConfig.
    Soporta cualquier API que retorne JSON con estructura similar a Socrata.
    """
    
    def transform(self, raw_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma JSON de API a registros validados (dirigido por config).
        
        Flujo:
          1. Obtener TransformationConfig de registry
          2. Parsear JSON rápido
          3. Extraer registros
          4. Aplicar validaciones vectorizadas
          5. Derivar columnas
          6. Mapear a fact + dimensiones
          7. Validar con Pydantic (solo válidas)
        """
        start_time = time.time()
        source_id = source_config.get("id")
        
        logger.info(f"[ApiTransformer] Iniciando transformación para {source_id}")
        
        # 1. Obtener configuracion
        transform_config = get_transformation_config(source_id)
        if not transform_config:
            logger.warning(f"[ApiTransformer] No hay TransformationConfig para {source_id}")
            return self._fallback_iterative([], source_id, start_time, "No hay configuración registrada")
        
        # 2. Parseo rapido
        if isinstance(raw_data, str):
            try:
                raw_data = _fast_json_loads(raw_data)
            except Exception as e:
                return self._error_response(start_time, str(e), raw_data)
        
        # # DEBUG: Mostrar estructura de raw_data
        # logger.debug(f"[ApiTransformer] raw_data tipo: {type(raw_data).__name__}")
        # if isinstance(raw_data, dict):
        #     logger.debug(f"[ApiTransformer] raw_data keys: {list(raw_data.keys())}")
        # elif isinstance(raw_data, list):
        #     logger.debug(f"[ApiTransformer] raw_data es lista con {len(raw_data)} items")

        # 3. Extraer registros
        records = self._extract_records(raw_data, transform_config)
        if records is None:
            if isinstance(raw_data, dict):
                sample_keys = list(raw_data.keys())[:5]
                logger.error(f"[ApiTransformer] Extracción fallida. data_path='{transform_config.data_path}', keys encontradas: {sample_keys}")
            elif isinstance(raw_data, list):
                logger.error(f"[ApiTransformer] Extracción fallida. data_path='{transform_config.data_path}', raw_data es lista de {len(raw_data)} items")
            else:
                logger.error(f"[ApiTransformer] Extracción fallida. raw_data tipo: {type(raw_data).__name__}")
            return self._error_response(start_time, f"Estructura JSON no coincide con data_path='{transform_config.data_path}'", raw_data)

        total_raw = len(records)
        if not records:
            return {
                "valid_records": [], "errors": [],
                "stats": {
                    "total_raw": 0, "valid": 0, "errors": 0,
                    "processing_time_seconds": time.time() - start_time,
                    "error_categories": {}
                }
            }

        # 4. Cargar DataFrame
        try:
            df = pd.DataFrame(records)
            df.columns = [c.strip() for c in df.columns]
        except Exception as e:
            return self._error_response(start_time, f"Error creando DataFrame: {e}", raw_data)
        
        # Inicializar acumulador de errores
        error_rows = []
        
        # 4.5. Limpieza comun
        # Este paso es comun para API, Web, Excel, etc.
        # logger.debug(f"[ApiTransformer] Aplicando limpieza común a DataFrame")
        try:
            df_clean, common_errors = DataValidator.validate_and_clean(
                df=df,
                records=records,
                not_null_columns=transform_config.not_null_columns,
                type_mapping=transform_config.type_mapping,
                normalize_strings=True
            )
            
            # Eliminar records correspondientes a filas con errores de limpieza
            error_indices = set(e["record_index"] for e in common_errors)
            if error_indices:
                # Crear mapeo de índices viejos a nuevos (después de eliminar filas)
                old_to_new_idx = {}
                new_idx = 0
                for old_idx in range(len(records)):
                    if old_idx not in error_indices:
                        old_to_new_idx[old_idx] = new_idx
                        new_idx += 1
                
                # Filtrar records
                records = [r for i, r in enumerate(records) if i not in error_indices]
            
            # Resetear indices para que coincidan con records
            df_clean = df_clean.reset_index(drop=True)
            df = df_clean
            error_rows.extend(common_errors)
            # logger.info(f"[ApiTransformer] Limpieza común completada: {len(df)} filas válidas, {len(common_errors)} errores detectados")
        except Exception as e:
            logger.warning(f"[ApiTransformer] Error en limpieza común: {e}")
            # Continuar con transformación incluso si limpieza parcial falla

        # 5. Pre-validaciones
        required_cols = set(vc.column for vc in transform_config.column_validations) | \
                       set(col for cd in transform_config.column_derivations for col in cd.source_columns)
        missing = required_cols - set(df.columns)
        if missing:
            return self._error_response(start_time, f"Columnas faltantes: {', '.join(missing)}", raw_data)
        
        for validation in transform_config.column_validations:
            error_rows.extend(self._apply_validation_rule(df, records, validation))

        invalid_indices = set(i for i in df.index if any(r["record_index"] == i for r in error_rows))
        df_valid = df.drop(index=list(invalid_indices)) if invalid_indices else df

        # 6. Derivar columnas
        for derivation in transform_config.column_derivations:
            try:
                df_valid[derivation.target_column] = df_valid.apply(derivation.function, axis=1)
            except Exception as e:
                logger.error(f"[ApiTransformer] Error derivando '{derivation.target_column}': {e}")
                for idx in df_valid.index:
                    error_rows.append({
                        "record_index": int(idx),
                        "error": f"Error derivando: {str(e)}",
                        "raw_record": records[idx]
                    })

        # 7. Mapeo y validacion final
        valid_records = []
        if transform_config.fact_mapping:
            for idx, row in df_valid.iterrows():
                try:
                    if transform_config.custom_validator:
                        custom_error = transform_config.custom_validator(row.to_dict())
                        if custom_error:
                            error_rows.append({
                                "record_index": int(idx), "error": custom_error,
                                "raw_record": row.to_dict()
                            })
                            continue
                    
                    if transform_config.custom_transformer:
                        record = transform_config.custom_transformer(row.to_dict(), source_id)
                    else:
                        record = self._build_record_from_config(row, transform_config, source_id)
                    
                    valid_records.append(record)
                except ValidationError as e:
                    error_rows.append({
                        "record_index": int(idx), "error": f"ValidationError: {str(e)}",
                        "raw_record": row.to_dict()
                    })
                except Exception as e:
                    error_rows.append({
                        "record_index": int(idx), "error": f"Error: {str(e)}",
                        "raw_record": row.to_dict()
                    })

        processing_time = time.time() - start_time
        error_categories = {}
        for er in error_rows:
            reason = er["error"].split("(")[0].strip()
            error_categories[reason] = error_categories.get(reason, 0) + 1

        logger.info(
            f"[ApiTransformer] Completada para {source_id}: "
            f"{len(valid_records)} válidos, {len(error_rows)} errores en {processing_time:.2f}s"
        )

        return {
            "valid_records": valid_records,
            "errors": error_rows,
            "stats": {
                "total_raw": total_raw,
                "valid": len(valid_records),
                "errors": len(error_rows),
                "processing_time_seconds": processing_time,
                "error_categories": error_categories
            }
        }
    
    def _extract_records(self, raw_data: Any, config) -> Optional[list]:
        """
        Extrae registros según data_path.
        
        Soporta:
        - data_path = "data" → raw_data["data"]
        - data_path = "result.records" → raw_data["result"]["records"]
        - data_path = None → raw_data si es lista directa
        """
        if config.data_path is None:
            # Lista directa de registros en raíz
            return raw_data if isinstance(raw_data, list) else None
        
        if not isinstance(raw_data, dict):
            logger.error(f"[ApiTransformer] raw_data no es dict, no se puede extraer con data_path='{config.data_path}'")
            return None
        
        # Soportar rutas anidadas: "result.records" → raw_data["result"]["records"]
        keys = config.data_path.split('.')
        current = raw_data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                logger.error(f"[ApiTransformer] data_path '{config.data_path}' no encontrado en estructura JSON. "
                           f"Keys disponibles en raíz: {list(raw_data.keys())}")
                return None
        
        # Validar que el resultado final es lista
        if not isinstance(current, list):
            logger.error(f"[ApiTransformer] data_path '{config.data_path}' no apunta a una lista. "
                       f"Tipo encontrado: {type(current).__name__}")
            return None
        
        return current
    
    def _apply_validation_rule(self, df: pd.DataFrame, records: list, validation) -> list:
        """Validación vectorizada."""
        errors = []
        col = validation.column
        if col not in df.columns:
            logger.debug(f"[ApiTransformer] Columna '{col}' no encontrada. Disponibles: {list(df.columns)[:10]}")
            return errors
        
        # Convertir a numerico si la validacion lo requiere
        if validation.rule in [ValidationRule.RANGE, ValidationRule.NON_NEGATIVE, ValidationRule.POSITIVE, ValidationRule.BETWEEN_0_100]:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception as e:
                logger.warning(f"[ApiTransformer] No se pudo convertir '{col}' a numérico: {e}")
        
        invalid_mask = None
        if validation.rule == ValidationRule.RANGE:
            min_v, max_v = validation.params.get("min"), validation.params.get("max")
            invalid_mask = ~df[col].between(min_v, max_v) if min_v is not None else None
        elif validation.rule == ValidationRule.ENUM:
            invalid_mask = ~df[col].isin(validation.params.get("values", []))
        elif validation.rule == ValidationRule.NON_NEGATIVE:
            invalid_mask = df[col] < 0
        elif validation.rule == ValidationRule.BETWEEN_0_100:
            invalid_mask = (df[col] < 0) | (df[col] > 100)
        
        if invalid_mask is not None:
            for idx in df[invalid_mask].index:
                errors.append({
                    "record_index": int(idx),
                    "error": validation.error_message,
                    "raw_record": records[idx]
                })
        return errors
    
    def _build_record_from_config(self, row: pd.Series, config, source_id: str) -> Dict[str, Any]:
        """Mapeo genérico desde config con sanitización de NaN."""
        mapping = config.fact_mapping
        
        # Construir fact_data con sanitizacion de NaN/Inf
        fact_data = {}
        for target, source in mapping.column_mapping.items():
            if source in row.index:
                value = _sanitize_value(row.get(source))
            else:
                value = source  # Valor literal (ej: "Bls/Kpc")
            fact_data[target] = value
        
        # Construir dimensions con sanitizacion
        dimensions = {}
        for dim in mapping.dimension_mappings:
            dim_data = {}
            for tf, sc in dim.column_mapping.items():
                if isinstance(sc, str) and sc in row.index:
                    dim_data[tf] = _sanitize_value(row.get(sc))
                else:
                    dim_data[tf] = sc  # Valor literal (ej: False para es_proyeccion)
            dimensions[dim.dimension_name] = dim_data
        
        return {"fact_table": mapping.fact_table, "data": fact_data, "dimensions": dimensions}
    
    def _error_response(self, start_time: float, msg: str, payload: Any) -> Dict[str, Any]:
        logger.error(f"[ApiTransformer] {msg}")
        return {
            "valid_records": [],
            "errors": [{"record_index": 0, "error": msg, "raw_record": payload}],
            "stats": {
                "total_raw": 0, "valid": 0, "errors": 1,
                "processing_time_seconds": time.time() - start_time,
                "error_categories": {msg: 1}
            }
        }

    def _fallback_iterative(self, records: list, source_id: str, start_time: float, reason: str = "") -> Dict[str, Any]:
        logger.warning(f"[ApiTransformer] Fallback para {source_id}: {reason}")
        return {
            "valid_records": [],
            "errors": [{"record_index": 0, "error": reason, "raw_record": None}],
            "stats": {
                "total_raw": len(records), "valid": 0, "errors": 1,
                "processing_time_seconds": time.time() - start_time,
                "error_categories": {}
            }
        }
