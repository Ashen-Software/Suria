"""
Transformer específico para MinMinas - Declaración de Producción de Gas Natural.

Extrae y transforma datos de archivos Excel de producción de gas.
Maneja tanto archivos individuales como lotes de archivos.
"""
import time
import re
from typing import Dict, Any, List, Optional, Tuple
from io import BytesIO
from datetime import date
from decimal import Decimal
from pydantic import ValidationError

from .base_source import BaseSourceTransformer, register_source_transformer
from ..schemas import FactOfertaGasSchema, TipoProduccionOferta, DimResolucionSchema
from ..custom_scripts.minminas_parser import MinMinasExcelParser, ProduccionRecord
from logs_config.logger import app_logger as logger


@register_source_transformer("minminas_oferta", "gas_natural_declaracion")
class MinMinasOfertaTransformer(BaseSourceTransformer):
    """
    Transformer para archivos Excel de MinMinas.
    
    Soporta:
    - Archivo Excel individual → fact_oferta_gas
    - Lote de archivos Excel → fact_oferta_gas + dim_resolucion
    """
    
    source_ids = ["minminas_oferta", "gas_natural_declaracion"]
    file_type = "excel"
    
    def transform(self, raw_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma un archivo Excel individual de MinMinas.
        
        Args:
            raw_data: Bytes del archivo Excel
            source_config: Configuración de la fuente
            
        Returns:
            Dict con valid_records, errors, stats
        """
        start_time = time.time()
        source_id = source_config.get("id", "minminas_oferta")
        
        logger.info(f"[MinMinasTransformer] Iniciando transformación para {source_id}")
        
        valid_records = []
        errors = []
        
        try:
            # Convertir a bytes si es necesario
            if hasattr(raw_data, 'read'):
                excel_bytes = raw_data.read()
            elif isinstance(raw_data, bytes):
                excel_bytes = raw_data
            else:
                excel_bytes = bytes(raw_data)
            
            # Parsear con el parser especializado
            parser = MinMinasExcelParser(excel_bytes, resolution_number=None)
            records, parse_errors = parser.parse()
            
            logger.info(
                f"[MinMinasTransformer] Parser: "
                f"{len(records)} registros, {len(parse_errors)} errores"
            )
            
            # Convertir ProduccionRecord a formato validado
            for record in records:
                try:
                    validated = self._validate_produccion_record(record, source_id)
                    valid_records.append(validated)
                except ValidationError as e:
                    errors.append({
                        "record": {
                            "campo": record.campo_nombre,
                            "operador": record.operador,
                            "tipo": record.tipo_produccion,
                            "anio": record.anio,
                            "mes": record.mes
                        },
                        "error": str(e)
                    })
            
            # Agregar errores del parser
            errors.extend(parse_errors)
            
        except Exception as e:
            logger.error(f"[MinMinasTransformer] Error leyendo Excel: {e}")
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
    
    def transform_batch(
        self, 
        excel_files: Dict[str, bytes], 
        metadata: Dict[str, Any],
        source_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transforma un lote de archivos Excel de MinMinas.
        
        Este método es específico para complex_scraper que genera
        múltiples archivos Excel (uno por resolución/campo).
        
        Args:
            excel_files: Dict {filename: bytes} con archivos Excel
            metadata: Metadata JSON con info de resoluciones
            source_config: Configuración de la fuente
            
        Returns:
            Dict con valid_records, errors, stats y resoluciones
        """
        start_time = time.time()
        source_id = source_config.get("id")
        
        logger.info(
            f"[MinMinasTransformer] Procesando lote: "
            f"{len(excel_files)} archivos Excel"
        )
        
        all_records = []
        all_errors = []
        resoluciones = []
        
        # Extraer info de resoluciones del metadata
        resolution_info = self._extract_resolution_info(metadata)
        
        for filename, excel_bytes in excel_files.items():
            try:
                # Extraer número de resolución del nombre de archivo
                resolution_number = self._extract_resolution_number(filename)
                
                logger.info(f"[MinMinasTransformer] Procesando {filename} (Resolución: {resolution_number})")
                
                # Parsear Excel
                parser = MinMinasExcelParser(excel_bytes, resolution_number)
                records, errors = parser.parse()
                
                # Convertir a formato validado
                for record in records:
                    try:
                        validated = self._validate_produccion_record(record, source_id)
                        all_records.append(validated)
                    except ValidationError as e:
                        all_errors.append({
                            "filename": filename,
                            "record": {
                                "campo": record.campo_nombre,
                                "operador": record.operador,
                                "tipo": record.tipo_produccion,
                                "anio": record.anio,
                                "mes": record.mes
                            },
                            "error": str(e)
                        })
                
                # Agregar errores del parser
                for error in errors:
                    error["filename"] = filename
                    all_errors.append(error)
                
                # Extraer info de resolución
                if resolution_number and resolution_number in resolution_info:
                    res_info = resolution_info[resolution_number]
                    if parser.metadata:
                        resoluciones.append({
                            "numero_resolucion": resolution_number,
                            "periodo_desde": parser.metadata.periodo_desde.isoformat(),
                            "periodo_hasta": parser.metadata.periodo_hasta.isoformat(),
                            "url_pdf": res_info.get("url_pdf"),
                            "url_soporte_magnetico": res_info.get("url_excel"),
                            "titulo": res_info.get("titulo")
                        })
                
                logger.info(
                    f"[MinMinasTransformer] {filename}: {len(records)} registros, "
                    f"{len(errors)} errores"
                )
                
            except Exception as e:
                logger.error(f"[MinMinasTransformer] Error procesando {filename}: {e}")
                all_errors.append({
                    "filename": filename,
                    "error": str(e),
                    "type": "file_error"
                })
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"[MinMinasTransformer] Lote completado: "
            f"{len(all_records)} registros válidos, {len(all_errors)} errores "
            f"en {processing_time:.2f}s"
        )
        
        return {
            "valid_records": all_records,
            "errors": all_errors,
            "resoluciones": resoluciones,
            "stats": {
                "total_files": len(excel_files),
                "total_raw": len(all_records) + len(all_errors),
                "valid": len(all_records),
                "errors": len(all_errors),
                "processing_time_seconds": processing_time
            }
        }
    
    def _validate_produccion_record(
        self, 
        record: ProduccionRecord, 
        source_id: str
    ) -> Dict[str, Any]:
        """
        Valida un ProduccionRecord con el schema Pydantic.
        
        Returns:
            Dict con formato para loader (fact_table, data, dimensions)
        """
        tiempo_fecha = date(record.anio, record.mes, 1)
        
        # Redondear valores a 6 decimales
        valor_gbtud = round(record.valor_gbtud, 6)
        poder_calorifico = round(record.poder_calorifico_btu_pc, 6) if record.poder_calorifico_btu_pc else None
        
        # Validar con schema
        fact_oferta = FactOfertaGasSchema(
            tiempo_fecha=tiempo_fecha,
            campo_nombre=record.campo_nombre,
            tipo_produccion=TipoProduccionOferta(record.tipo_produccion),
            operador=record.operador,
            es_operador_campo=not record.es_participacion_estado,
            es_participacion_estado=record.es_participacion_estado,
            valor_gbtud=Decimal(str(valor_gbtud)),
            poder_calorifico_btu_pc=Decimal(str(poder_calorifico)) if poder_calorifico else None,
            resolucion_number=record.resolucion_number,
            source_id=source_id
        )
        
        return {
            "fact_table": "fact_oferta_gas",
            "data": fact_oferta.model_dump(),
            "dimensions": {
                "tiempo": {
                    "fecha": tiempo_fecha,
                    "anio": record.anio,
                    "mes": record.mes,
                    "es_proyeccion": False
                },
                "campo": {
                    "nombre_campo": record.campo_nombre,
                    "activo": True
                },
                "resolucion": {
                    "numero_resolucion": record.resolucion_number
                }
            }
        }
    
    def _extract_resolution_number(self, filename: str) -> Optional[str]:
        """Extrae número de resolución del nombre de archivo."""
        # Formato esperado: res_00014.xlsm o res_00014.xlsx
        match = re.search(r'res_(\d+)', filename, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def _extract_resolution_info(self, metadata: Dict[str, Any]) -> Dict[str, Dict]:
        """
        Extrae información de resoluciones del metadata.
        
        Retorna dict {numero_resolucion: {url_pdf, url_excel, titulo}}
        """
        result = {}
        
        declarations = metadata.get("declarations", [])
        for declaration in declarations:
            resolutions = declaration.get("resolutions", [])
            for resolution in resolutions:
                number = resolution.get("number")
                if not number:
                    continue
                
                result[number] = {
                    "url_pdf": resolution.get("url"),
                    "titulo": resolution.get("title"),
                    "fecha": resolution.get("date")
                }
                
                # Buscar URL del Excel en soporte_magnetico
                soportes = resolution.get("soporte_magnetico", [])
                if isinstance(soportes, list):
                    for soporte in soportes:
                        if soporte and soporte.get("bucket_path"):
                            result[number]["url_excel"] = soporte.get("url")
                            break
        
        return result
