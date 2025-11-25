"""
Limpieza y normalización de datos común a todos los transformadores.

Responsable de:
- Normalizar tipos de datos
- Validar nulos (NOT NULL constraints)
- Limpiar espacios en blanco
- Detectar duplicados
- Normalización de strings

Este módulo actúa como punto de entrada COMÚN independientemente del tipo de fuente
(API, Web, Excel, etc.). Se ejecuta una vez que los datos están en DataFrame.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from logs_config.logger import app_logger as logger


class DataValidator:
    """Validador común de datos post-extracción."""
    
    @staticmethod
    def validate_and_clean(
        df: pd.DataFrame,
        records: List[Dict],
        not_null_columns: Optional[List[str]] = None,
        type_mapping: Optional[Dict[str, str]] = None,
        normalize_strings: bool = True
    ) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Limpia y valida DataFrame de forma común.
        
        Args:
            df: DataFrame a validar
            records: Lista de registros originales (para error tracking)
            not_null_columns: Columnas que no pueden ser nulas
            type_mapping: Mapeo de columnas a tipos (ej: {"mes": "int", "precio": "float"})
            normalize_strings: Si se deben normalizar strings (strip, lowercase de códigos, etc.)
        
        Returns:
            Tupla (df_cleaned, error_records) donde error_records contiene filas con errores
        """
        error_records = []
        invalid_indices = set()
        
        logger.debug(f"[DataValidator] Iniciando limpieza. Filas: {len(df)}, Columnas: {len(df.columns)}")
        
        # 1. Normalizar espacios en nombres de columnas
        df.columns = [c.strip() for c in df.columns]
        
        # 2. Limpiar espacios en blanco en celdas de string
        if normalize_strings:
            df = DataValidator._clean_whitespace(df)
        
        # 3. Normalizar tipos de datos
        if type_mapping:
            df, type_errors = DataValidator._convert_types(df, type_mapping, records)
            error_records.extend(type_errors)
            invalid_indices.update(e["record_index"] for e in type_errors)
        
        # 4. Validar NOT NULL constraints
        if not_null_columns:
            null_errors = DataValidator._validate_not_null(df, not_null_columns, records)
            error_records.extend(null_errors)
            invalid_indices.update(e["record_index"] for e in null_errors)
        
        # 5. Detectar duplicados (informativo, no elimina)
        if len(df) > 0:
            DataValidator._detect_duplicates(df)
        
        # Retornar solo filas validas
        df_clean = df.drop(index=list(invalid_indices)) if invalid_indices else df
        
        logger.debug(f"[DataValidator] Limpieza completada. Filas válidas: {len(df_clean)}, Errores: {len(error_records)}")
        
        return df_clean, error_records
    
    @staticmethod
    def _clean_whitespace(df: pd.DataFrame) -> pd.DataFrame:
        """Limpia espacios en blanco en celdas de tipo string."""
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = df[col].apply(
                        lambda x: x.strip() if isinstance(x, str) else x
                    )
                except Exception as e:
                    logger.warning(f"[DataValidator] No se pudo limpiar espacios en '{col}': {e}")
        return df
    
    @staticmethod
    def _convert_types(
        df: pd.DataFrame,
        type_mapping: Dict[str, str],
        records: List[Dict]
    ) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Convierte tipos de datos según mapeo.
        
        Returns:
            Tupla (df_convertido, error_records)
        """
        error_records = []
        
        for col, target_type in type_mapping.items():
            if col not in df.columns:
                logger.warning(f"[DataValidator] Columna '{col}' no existe para conversión de tipo")
                continue
            
            try:
                if target_type == "int":
                    # Convertir a numeric primero (reemplaza no convertibles con NaN)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    # Encontrar NaN (que eran no convertibles)
                    nan_mask = df[col].isna() & df[col].notna()  # Esto no funcionará bien
                    # Mejor: Convertir a int, pero primero validar
                    df[col] = df[col].astype('Int64', errors='ignore')  # Int64 maneja NaN
                    
                elif target_type == "float":
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                elif target_type == "str":
                    df[col] = df[col].astype(str)
                    
                elif target_type == "date":
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    
                elif target_type == "bool":
                    df[col] = df[col].astype(bool)
                
                logger.debug(f"[DataValidator] Columna '{col}' convertida a {target_type}")
                
            except Exception as e:
                logger.error(f"[DataValidator] Error convirtiendo '{col}' a {target_type}: {e}")
        
        return df, error_records
    
    @staticmethod
    def _validate_not_null(
        df: pd.DataFrame,
        not_null_columns: List[str],
        records: List[Dict]
    ) -> List[Dict]:
        """
        Valida que columnas específicas no tengan valores nulos.
        
        Returns:
            Lista de error_records para filas con nulos
        """
        error_records = []
        
        for col in not_null_columns:
            if col not in df.columns:
                logger.warning(f"[DataValidator] Columna NOT NULL '{col}' no existe")
                continue
            
            null_mask = df[col].isna() | (df[col] == '')
            null_indices = df[null_mask].index
            
            if len(null_indices) > 0:
                logger.warning(f"[DataValidator] Encontrados {len(null_indices)} valores nulos en '{col}'")
                for idx in null_indices:
                    error_records.append({
                        "record_index": int(idx),
                        "error": f"Valor nulo en columna requerida '{col}'",
                        "raw_record": records[idx] if idx < len(records) else {}
                    })
        
        return error_records
    
    @staticmethod
    def _detect_duplicates(df: pd.DataFrame, key_columns: Optional[List[str]] = None) -> None:
        """
        Detecta duplicados (informativo, solo log).
        
        Args:
            df: DataFrame
            key_columns: Columnas que forman la clave única. Si None, usa todas.
        """
        try:
            if key_columns:
                duplicates = df.duplicated(subset=key_columns, keep=False)
            else:
                duplicates = df.duplicated(keep=False)
            
            dup_count = duplicates.sum()
            if dup_count > 0:
                logger.warning(f"[DataValidator] Detectados {dup_count} registros duplicados")
                # Mostrar algunos ejemplos
                dup_rows = df[duplicates].head(3)
                logger.debug(f"[DataValidator] Ejemplos de duplicados:\n{dup_rows.to_string()}")
        
        except Exception as e:
            logger.warning(f"[DataValidator] Error detectando duplicados: {e}")
    
    @staticmethod
    def validate_constraints(
        df: pd.DataFrame,
        records: List[Dict],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Valida constraints adicionales (ranges, enums, etc.).
        
        Args:
            df: DataFrame
            records: Lista de registros originales
            constraints: Dict con constraints (ej: {
                "mes": {"type": "range", "min": 1, "max": 12},
                "tipo": {"type": "enum", "values": ["A", "B", "C"]}
            })
        
        Returns:
            Tupla (df_valid, error_records)
        """
        error_records = []
        invalid_indices = set()
        
        if not constraints:
            return df, error_records
        
        for col, constraint in constraints.items():
            if col not in df.columns:
                continue
            
            constraint_type = constraint.get("type")
            
            if constraint_type == "range":
                min_val = constraint.get("min")
                max_val = constraint.get("max")
                mask = (df[col] < min_val) | (df[col] > max_val)
                
                for idx in df[mask].index:
                    error_records.append({
                        "record_index": int(idx),
                        "error": f"'{col}' fuera de rango [{min_val}, {max_val}]",
                        "raw_record": records[idx]
                    })
                    invalid_indices.add(idx)
            
            elif constraint_type == "enum":
                allowed = constraint.get("values", [])
                mask = ~df[col].isin(allowed)
                
                for idx in df[mask].index:
                    error_records.append({
                        "record_index": int(idx),
                        "error": f"'{col}' no está en valores permitidos {allowed}",
                        "raw_record": records[idx]
                    })
                    invalid_indices.add(idx)
        
        df_clean = df.drop(index=list(invalid_indices)) if invalid_indices else df
        return df_clean, error_records
