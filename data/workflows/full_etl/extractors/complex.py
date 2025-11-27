from typing import Dict, Any
from datetime import datetime
from .base import BaseExtractor
from extraction.scrapers.scraper_loader import run_scraper_loader
from services.backend_client import BackendClient
from logs_config.logger import app_logger as logger
import json

class ComplexScraperExtractor(BaseExtractor):
    """
    Extractor para scrapers complejos que pueden retornar múltiples archivos.
    
    Soporta dos formatos de retorno del scraper:
    
    1. Formato simple (bytes/str): Se guarda como un único archivo JSON
    
    2. Formato estructurado (dict): Para fuentes con múltiples archivos
       {
           "metadata": bytes,  # JSON con metadata
           "excel_files": [    # Archivos Excel originales
               {"filename": str, "content": bytes, "parsed_data": dict|None},
               ...
           ]
       }
       
       Estructura en bucket:
       complex/{source_id}/{timestamp}/
           metadata.json
           excel/
               res_00739.xlsx
               res_01281.xlsx
           parsed/
               res_00739.json
               res_01281.json
    """
    
    def extract(self, source_config: Dict[str, Any]):
        src_id = source_config.get("id")
        logger.info(f"[ComplexScraperExtractor] Delegando extracción de {src_id} a script custom")
        
        try:
            # Llama al loader con action='extract'
            result = run_scraper_loader(source_config, action="extract")
            
            if not result:
                logger.warning(f"[ComplexScraperExtractor] No se obtuvo resultado de {src_id}")
                return
            
            storage_config = source_config.get("storage", {})
            bucket_name = storage_config.get("bucket", "raw-data")
            path_prefix = storage_config.get("path_prefix", f"complex/{src_id}")
            
            # Generar timestamp para este lote
            now = datetime.now()
            timestamp_path = now.strftime("%Y-%m-%d_%H%M%S")
            
            client = BackendClient()
            
            # Detectar formato del resultado
            if isinstance(result, dict) and "metadata" in result:
                # Formato estructurado: multiples archivos
                self._upload_structured_result(
                    client, result, bucket_name, path_prefix, timestamp_path, src_id
                )
            else:
                # Formato simple: un unico archivo
                self._upload_simple_result(
                    client, result, bucket_name, path_prefix, timestamp_path, src_id
                )
                
        except Exception as e:
            logger.error(f"[ComplexScraperExtractor] Error en extracción compleja de {src_id}: {e}")
            import traceback
            traceback.print_exc()
    
    def _upload_simple_result(
        self, 
        client: BackendClient, 
        result: Any, 
        bucket_name: str, 
        path_prefix: str, 
        timestamp: str,
        src_id: str
    ):
        """Sube resultado simple como un único archivo JSON."""
        remote_path = f"{path_prefix}/{timestamp}.json"
        
        content = result
        if isinstance(result, str):
            content = result.encode('utf-8')
        
        client.upload_file(bucket_name, remote_path, content, "application/json")
        logger.info(f"[ComplexScraperExtractor] Archivo guardado en {bucket_name}/{remote_path}")
    
    def _upload_structured_result(
        self, 
        client: BackendClient, 
        result: Dict[str, Any], 
        bucket_name: str, 
        path_prefix: str, 
        timestamp: str,
        src_id: str
    ):
        """
        Sube resultado estructurado con múltiples archivos.
        
        Estructura:
        {path_prefix}/{timestamp}/
            metadata.json
            excel/*.xlsx
            parsed/*.json
        """
        base_path = f"{path_prefix}/{timestamp}"
        files_uploaded = 0
        
        # 1. Subir metadata.json
        metadata = result.get("metadata")
        if metadata:
            metadata_path = f"{base_path}/metadata.json"
            content = metadata if isinstance(metadata, bytes) else metadata.encode('utf-8')
            client.upload_file(bucket_name, metadata_path, content, "application/json")
            logger.info(f"[ComplexScraperExtractor] Metadata: {bucket_name}/{metadata_path}")
            files_uploaded += 1
        
        # 2. Subir archivos Excel originales
        excel_files = result.get("excel_files", [])
        for excel_file in excel_files:
            filename = excel_file.get("filename")
            content = excel_file.get("content")
            
            if filename and content:
                # Subir Excel original
                excel_path = f"{base_path}/excel/{filename}"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                if filename.endswith(".xlsm"):
                    content_type = "application/vnd.ms-excel.sheet.macroEnabled.12"
                elif filename.endswith(".xls"):
                    content_type = "application/vnd.ms-excel"
                
                client.upload_file(bucket_name, excel_path, content, content_type)
                logger.info(f"[ComplexScraperExtractor] Excel: {bucket_name}/{excel_path}")
                files_uploaded += 1
                
                # Subir datos parseados si existen
                parsed_data = excel_file.get("parsed_data")
                if parsed_data:
                    parsed_filename = filename.rsplit(".", 1)[0] + ".json"
                    parsed_path = f"{base_path}/parsed/{parsed_filename}"
                    parsed_content = json.dumps(parsed_data, ensure_ascii=False, indent=2).encode('utf-8')
                    client.upload_file(bucket_name, parsed_path, parsed_content, "application/json")
                    logger.info(f"[ComplexScraperExtractor] Parsed: {bucket_name}/{parsed_path}")
                    files_uploaded += 1
        
        logger.info(
            f"[ComplexScraperExtractor] Extracción completada para {src_id}: "
            f"{files_uploaded} archivos subidos a {bucket_name}/{base_path}/"
        )
