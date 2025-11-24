from typing import Dict, Any
from datetime import datetime
from .base import BaseExtractor
from extraction.scrapers.scraper_loader import run_scraper_loader
from services.backend_client import BackendClient
from logs_config.logger import app_logger as logger

class ComplexScraperExtractor(BaseExtractor):
    def extract(self, source_config: Dict[str, Any]):
        src_id = source_config.get("id")
        logger.info(f"[ComplexScraperExtractor] Delegando extracción de {src_id} a script custom")
        
        try:
            # Llama al loader con action='extract'
            # Se espera que el script retorne el contenido del archivo (bytes o str)
            result = run_scraper_loader(source_config, action="extract")
            
            if result:
                storage_config = source_config.get("storage", {})
                bucket_name = storage_config.get("bucket", "raw-data")
                
                # Generar path historico por defecto: complex/{id}/YYYY-MM-DD_HHMMSS.bin
                now = datetime.now()
                timestamp_path = now.strftime("%Y-%m-%d_%H%M%S")
                default_path = f"complex/{src_id}/{timestamp_path}.bin"
                
                remote_path = storage_config.get("path", default_path)
                
                content = result
                if isinstance(result, str):
                    content = result.encode('utf-8')
                
                client = BackendClient()
                client.upload_file(bucket_name, remote_path, content)
                
        except Exception as e:
            logger.error(f"[ComplexScraperExtractor] Error en extracción compleja de {src_id}: {e}")
