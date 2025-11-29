"""
Transformer genérico para archivos Excel.

Este transformer maneja la lectura de archivos Excel y delega
la transformación específica a los source transformers registrados.

Para lógica específica de una fuente, crear un transformer en:
    transformers/source_transformers/{source_id}.py
"""
import time
from typing import Dict, Any, List, Optional
from io import BytesIO
import pandas as pd
from .base import BaseTransformer
from logs_config.logger import app_logger as logger


class ExcelTransformer(BaseTransformer):
    """
    Transforma archivos Excel a estructura normalizada.
    
    Este es un transformer GENÉRICO. Para lógica específica de fuentes
    como MinMinas o UPME, ver:
    - source_transformers/minminas_oferta.py
    - source_transformers/upme_demanda.py
    
    Uso:
    - Si source_id tiene un source_transformer registrado, úsalo directamente
    - Este transformer es el fallback para Excel sin lógica específica
    """
    
    def transform(self, raw_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma Excel a registros.
        
        Intenta usar un source transformer específico si existe,
        sino aplica transformación genérica.
        
        Args:
            raw_data: Bytes del archivo Excel o path al archivo
            source_config: Configuración de la fuente
            
        Returns:
            Diccionario con valid_records, errors y stats
        """
        start_time = time.time()
        source_id = source_config.get("id")
        
        logger.info(f"[ExcelTransformer] Iniciando transformación para {source_id}")
        
        # Intentar usar source transformer específico
        from .source_transformers.base_source import get_source_transformer
        source_transformer = get_source_transformer(source_id)
        
        if source_transformer:
            logger.info(f"[ExcelTransformer] Delegando a transformer específico: {source_id}")
            return source_transformer.transform(raw_data, source_config)
        
        # Fallback: transformacion generica
        logger.warning(
            f"[ExcelTransformer] No hay transformer específico para {source_id}. "
            "Usando transformación genérica."
        )
        
        return self._transform_generic_excel(raw_data, source_id, start_time)
    
    def transform_batch(
        self, 
        excel_files: Dict[str, bytes], 
        metadata: Dict[str, Any],
        source_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transforma un lote de archivos Excel.
        
        Delega al source transformer específico si existe.
        
        Args:
            excel_files: Dict {filename: bytes} con archivos Excel
            metadata: Metadata JSON con info adicional
            source_config: Configuración de la fuente
            
        Returns:
            Dict con valid_records, errors, stats
        """
        source_id = source_config.get("id")
        
        # Intentar usar source transformer especofico
        from .source_transformers.base_source import get_source_transformer
        source_transformer = get_source_transformer(source_id)
        
        if source_transformer and hasattr(source_transformer, 'transform_batch'):
            logger.info(f"[ExcelTransformer] Delegando batch a: {source_id}")
            return source_transformer.transform_batch(excel_files, metadata, source_config)
        
        # Fallback: procesar cada archivo individualmente
        logger.warning(
            f"[ExcelTransformer] No hay batch transformer para {source_id}. "
            "Procesando archivos individualmente."
        )
        
        all_records = []
        all_errors = []
        start_time = time.time()
        
        for filename, excel_bytes in excel_files.items():
            result = self.transform(excel_bytes, source_config)
            all_records.extend(result.get("valid_records", []))
            
            # Agregar filename a cada error
            for error in result.get("errors", []):
                error["filename"] = filename
                all_errors.append(error)
        
        return {
            "valid_records": all_records,
            "errors": all_errors,
            "stats": {
                "total_files": len(excel_files),
                "total_raw": len(all_records) + len(all_errors),
                "valid": len(all_records),
                "errors": len(all_errors),
                "processing_time_seconds": time.time() - start_time
            }
        }
    
    def _transform_generic_excel(
        self, 
        raw_data: Any, 
        source_id: str,
        start_time: float
    ) -> Dict[str, Any]:
        """
        Transformación genérica para Excel sin schema específico.
        
        Lee la primera hoja y retorna los datos como diccionarios.
        Útil para debugging o fuentes nuevas sin schema definido.
        
        Args:
            raw_data: Archivo Excel (bytes o BytesIO)
            source_id: ID de la fuente
            start_time: Tiempo de inicio para calcular duración
            
        Returns:
            Dict con valid_records, errors, stats
        """
        valid_records = []
        errors = []
        
        try:
            # Preparar archivo
            if isinstance(raw_data, bytes):
                excel_file = BytesIO(raw_data)
            else:
                excel_file = raw_data
            
            df = pd.read_excel(excel_file, sheet_name=0, engine='openpyxl')
            
            logger.info(f"[ExcelTransformer] Leyendo {len(df)} filas (transformación genérica)")
            
            for idx, row in df.iterrows():
                valid_records.append({
                    "fact_table": "unknown",
                    "data": row.to_dict(),
                    "dimensions": {},
                    "_source_id": source_id,
                    "_row_index": idx
                })
                
        except Exception as e:
            logger.error(f"[ExcelTransformer] Error leyendo Excel: {e}")
            errors.append({
                "record_index": 0,
                "error": str(e),
                "raw_record": None
            })
        
        processing_time = time.time() - start_time
        
        return {
            "valid_records": valid_records,
            "errors": errors,
            "stats": {
                "total_raw": len(valid_records) + len(errors),
                "valid": len(valid_records),
                "errors": len(errors),
                "processing_time_seconds": processing_time
            }
        }
    
    # utils
    def read_excel_sheets(
        self, 
        raw_data: Any, 
        sheet_name: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Lee hojas de un archivo Excel.
        
        Método utilitario que pueden usar los source transformers.
        
        Args:
            raw_data: Bytes o BytesIO del Excel
            sheet_name: Nombre de hoja específica o None para todas
            
        Returns:
            Dict {sheet_name: DataFrame}
        """
        if isinstance(raw_data, bytes):
            excel_file = BytesIO(raw_data)
        else:
            excel_file = raw_data
        
        if sheet_name:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl')
            return {sheet_name: df}
        else:
            return pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
    
    @staticmethod
    def convert_to_gbtud(valor: float, unidad: str) -> Optional[float]:
        """
        Convierte valores entre unidades de gas.
        
        Factores de conversión:
        - GBTUD → 1.0
        - KPCD → 0.001
        - MPCD → 1.0
        
        Args:
            valor: Valor a convertir
            unidad: Unidad origen
            
        Returns:
            Valor convertido a GBTUD o None si unidad no reconocida
        """
        factores = {
            "GBTUD": 1.0,
            "KPCD": 0.001,
            "MPCD": 1.0,
            "KPC": 0.001,
        }
        
        factor = factores.get(unidad.upper())
        if factor is None:
            logger.warning(f"Unidad '{unidad}' no reconocida para conversión a GBTUD")
            return None
        
        return valor * factor
