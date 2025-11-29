"""
Transformer específico para UPME - Proyección de Demanda de Gas.

Transforma archivos Excel de proyección de demanda a fact_demanda_gas.
"""
import time
from typing import Dict, Any, List
from datetime import date
import pandas as pd
from pydantic import ValidationError

from .base_source import BaseSourceTransformer, register_source_transformer
from ..schemas import FactDemandaGasSchema
from logs_config.logger import app_logger as logger


@register_source_transformer("upme_demanda")
class UpmeDemandaTransformer(BaseSourceTransformer):
    """
    Transformer para archivos Excel de UPME (proyección de demanda).
    
    Estructura esperada del Excel:
    - Múltiples hojas (una por escenario o región)
    - Columnas: Año, Mes, Escenario, Sector, Region, Segmento, Demanda_GBTUD
    """
    
    source_ids = ["upme_demanda"]
    file_type = "excel"
    
    def transform(self, raw_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma Excel de UPME a fact_demanda_gas.
        
        Args:
            raw_data: Bytes del archivo Excel
            source_config: Configuración de la fuente
            
        Returns:
            Dict con valid_records, errors, stats
        """
        start_time = time.time()
        source_id = source_config.get("id", "upme_demanda")
        
        logger.info(f"[UpmeDemandaTransformer] Iniciando transformación para {source_id}")
        
        valid_records = []
        errors = []
        
        try:
            # Leer todas las hojas del Excel
            excel_sheets = pd.read_excel(raw_data, sheet_name=None, engine='openpyxl')
            
            for sheet_name, df in excel_sheets.items():
                logger.info(f"[UpmeDemandaTransformer] Procesando hoja '{sheet_name}' con {len(df)} filas")
                
                # Normalizar nombres de columnas
                df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
                
                # Convertir cada fila
                for idx, row in df.iterrows():
                    try:
                        record = self._transform_row(row, source_id)
                        valid_records.append(record)
                        
                    except ValidationError as e:
                        errors.append({
                            "record_index": idx,
                            "sheet": sheet_name,
                            "error": str(e),
                            "raw_record": row.to_dict()
                        })
                    except Exception as e:
                        errors.append({
                            "record_index": idx,
                            "sheet": sheet_name,
                            "error": f"Error inesperado: {str(e)}",
                            "raw_record": row.to_dict()
                        })
            
        except Exception as e:
            logger.error(f"[UpmeDemandaTransformer] Error leyendo Excel: {e}")
            errors.append({
                "record_index": 0,
                "error": f"Error leyendo archivo: {str(e)}",
                "raw_record": None
            })
        
        return self._create_result(
            valid_records=valid_records,
            errors=errors,
            processing_time=time.time() - start_time
        )
    
    def _transform_row(self, row: pd.Series, source_id: str) -> Dict[str, Any]:
        """
        Transforma una fila del Excel a registro validado.
        
        Args:
            row: Fila del DataFrame
            source_id: ID de la fuente
            
        Returns:
            Dict con formato para loader
            
        Raises:
            ValidationError: Si el registro no cumple el schema
        """
        # Construir fecha
        anio = int(row.get('anio', row.get('año', 0)))
        mes = int(row.get('mes', 1))
        tiempo_fecha = date(anio, mes, 1)
        
        # Validar con schema
        fact_demanda = FactDemandaGasSchema(
            tiempo_fecha=tiempo_fecha,
            escenario=row['escenario'].upper(),
            sector=row['sector'].upper(),
            region=row['region'].upper(),
            segmento=row['segmento'].upper(),
            nivel_agregacion=row.get('nivel_agregacion', 'nacional').lower(),
            valor_demanda_gbtud=float(row['demanda_gbtud']),
            source_id=source_id
        )
        
        return {
            "fact_table": "fact_demanda_gas",
            "data": fact_demanda.model_dump(),
            "dimensions": {
                "tiempo": {
                    "fecha": tiempo_fecha,
                    "anio": anio,
                    "mes": mes,
                    "es_proyeccion": True
                }
            }
        }
