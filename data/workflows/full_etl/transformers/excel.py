"""
Transformer para archivos Excel (UPME, MinMinas).

Parsea archivos Excel descargados y los transforma a estructura
normalizada para fact_demanda_gas y fact_oferta_gas.
"""
import time
from typing import Dict, Any, List, Optional
from io import BytesIO
import pandas as pd
from .base import BaseTransformer
from .schemas import FactDemandaGasSchema, FactOfertaGasSchema
from logs_config.logger import app_logger as logger
from pydantic import ValidationError


class ExcelTransformer(BaseTransformer):
    """
    Transforma archivos Excel a estructura normalizada.
    
    Soporta:
    - UPME Proyección Demanda → fact_demanda_gas
    - MinMinas Declaración Producción → fact_oferta_gas
    """
    
    def transform(self, raw_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma Excel a registros validados.
        
        Args:
            raw_data: Bytes del archivo Excel o path al archivo
            source_config: Configuración de la fuente
            
        Returns:
            Diccionario con valid_records, errors y stats
        """
        start_time = time.time()
        source_id = source_config.get("id")
        
        logger.info(f"[ExcelTransformer] Iniciando transformación para {source_id}")
        
        # Determinar tipo de fuente
        transformer_fn = self._get_transformer_function(source_id)
        
        try:
            # Leer Excel (puede tener multiples hojas)
            if isinstance(raw_data, bytes):
                excel_file = BytesIO(raw_data)
            else:
                excel_file = raw_data
            
            # Parsear segun tipo de fuente
            valid_records, errors = transformer_fn(excel_file, source_id)
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"[ExcelTransformer] Transformación completada para {source_id}: "
                f"{len(valid_records)} válidos, {len(errors)} errores en {processing_time:.2f}s"
            )
            
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
            
        except Exception as e:
            logger.exception(f"[ExcelTransformer] Error crítico transformando {source_id}: {e}")
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
    
    def _get_transformer_function(self, source_id: str):
        """
        Retorna la función de transformación apropiada según el source_id.
        
        Args:
            source_id: Identificador de la fuente
            
        Returns:
            Función que transforma Excel → (valid_records, errors)
        """
        transformers = {
            "upme_demanda": self._transform_upme_demanda,
            "minminas_oferta": self._transform_minminas_oferta,
        }
        
        return transformers.get(source_id, self._transform_generic_excel)
    
    def _transform_upme_demanda(self, excel_file: Any, source_id: str) -> tuple[List[Dict], List[Dict]]:
        """
        Transforma Excel de UPME (proyección de demanda) a fact_demanda_gas.
        
        Estructura esperada del Excel:
        - Múltiples hojas (una por escenario o región)
        - Columnas: Año, Mes, Escenario, Sector, Region, Segmento, Demanda_GBTUD
        
        Args:
            excel_file: Archivo Excel
            source_id: ID de la fuente
            
        Returns:
            Tupla (valid_records, errors)
        """
        valid_records = []
        errors = []
        
        try:
            # Leer todas las hojas del Excel
            excel_sheets = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
            
            for sheet_name, df in excel_sheets.items():
                logger.info(f"[ExcelTransformer] Procesando hoja '{sheet_name}' con {len(df)} filas")
                
                # Normalizar nombres de columnas (minúsculas, sin espacios)
                df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
                
                # Convertir cada fila a registro
                for idx, row in df.iterrows():
                    try:
                        # Extraer datos
                        from datetime import date
                        
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
                        
                        valid_records.append({
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
                        })
                        
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
            logger.error(f"[ExcelTransformer] Error leyendo Excel UPME: {e}")
            errors.append({
                "record_index": 0,
                "error": f"Error leyendo archivo: {str(e)}",
                "raw_record": None
            })
        
        return valid_records, errors
    
    def _transform_minminas_oferta(self, excel_file: Any, source_id: str) -> tuple[List[Dict], List[Dict]]:
        """
        Transforma Excel de MinMinas (declaración de producción) a fact_oferta_gas.
        
        Estructura esperada:
        - Columnas: Año, Mes, Campo, Contrato, Operador, Potencial_Produccion, Unidad
        
        Args:
            excel_file: Archivo Excel
            source_id: ID de la fuente
            
        Returns:
            Tupla (valid_records, errors)
        """
        valid_records = []
        errors = []
        
        try:
            # Leer Excel (primera hoja por defecto)
            df = pd.read_excel(excel_file, sheet_name=0, engine='openpyxl')
            
            logger.info(f"[ExcelTransformer] Procesando MinMinas Oferta con {len(df)} filas")
            
            # Normalizar nombres de columnas
            df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
            
            for idx, row in df.iterrows():
                try:
                    from datetime import date
                    
                    # Construir fecha
                    anio = int(row.get('anio', row.get('año', 0)))
                    mes = int(row.get('mes', 1))
                    tiempo_fecha = date(anio, mes, 1)
                    
                    # Extraer unidad y potencial
                    unidad = str(row.get('unidad', 'KPCD')).upper()
                    potencial = float(row['potencial_produccion'])
                    
                    # Convertir a GBTUD usando factores de conversión
                    potencial_gbtud = self._convert_to_gbtud(potencial, unidad)
                    
                    # Validar con schema
                    fact_oferta = FactOfertaGasSchema(
                        tiempo_fecha=tiempo_fecha,
                        campo_nombre=str(row['campo']).strip(),
                        potencial_produccion=potencial,
                        unidad=unidad,
                        potencial_gbtud=potencial_gbtud,
                        source_id=source_id
                    )
                    
                    valid_records.append({
                        "fact_table": "fact_oferta_gas",
                        "data": fact_oferta.model_dump(),
                        "dimensions": {
                            "tiempo": {
                                "fecha": tiempo_fecha,
                                "anio": anio,
                                "mes": mes,
                                "es_proyeccion": False
                            },
                            "campo": {
                                "nombre_campo": fact_oferta.campo_nombre,
                                "contrato": row.get('contrato'),
                                "operador": row.get('operador'),
                                "activo": True
                            }
                        }
                    })
                    
                except ValidationError as e:
                    errors.append({
                        "record_index": idx,
                        "error": str(e),
                        "raw_record": row.to_dict()
                    })
                except Exception as e:
                    errors.append({
                        "record_index": idx,
                        "error": f"Error inesperado: {str(e)}",
                        "raw_record": row.to_dict()
                    })
            
        except Exception as e:
            logger.error(f"[ExcelTransformer] Error leyendo Excel MinMinas: {e}")
            errors.append({
                "record_index": 0,
                "error": f"Error leyendo archivo: {str(e)}",
                "raw_record": None
            })
        
        return valid_records, errors
    
    def _convert_to_gbtud(self, valor: float, unidad: str) -> Optional[float]:
        """
        Convierte valores entre unidades usando factores de conversión.
        
        Factores de conversión (según ref_unidades):
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
            "KPC": 0.001,  # Por día
        }
        
        factor = factores.get(unidad.upper())
        if factor is None:
            logger.warning(f"[ExcelTransformer] Unidad '{unidad}' no reconocida. No se puede convertir a GBTUD.")
            return None
        
        return valor * factor
    
    def _transform_generic_excel(self, excel_file: Any, source_id: str) -> tuple[List[Dict], List[Dict]]:
        """
        Transformación genérica para Excel sin schema específico.
        Lee la primera hoja y retorna los datos como diccionarios.
        
        Args:
            excel_file: Archivo Excel
            source_id: ID de la fuente
            
        Returns:
            Tupla (valid_records, errors)
        """
        logger.warning(
            f"[ExcelTransformer] Usando transformación genérica para {source_id}. "
            "Considere implementar schema específico."
        )
        
        valid_records = []
        errors = []
        
        try:
            df = pd.read_excel(excel_file, sheet_name=0)
            
            for idx, row in df.iterrows():
                valid_records.append({
                    "fact_table": "unknown",
                    "data": row.to_dict(),
                    "dimensions": {}
                })
        except Exception as e:
            errors.append({
                "record_index": 0,
                "error": str(e),
                "raw_record": None
            })
        
        return valid_records, errors
