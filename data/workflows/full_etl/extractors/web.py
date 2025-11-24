from typing import Dict, Any
import requests
import os
from datetime import datetime
from .base import BaseExtractor
from services.backend_client import BackendClient
from logs_config.logger import app_logger as logger

class WebScraperExtractor(BaseExtractor):
    def extract(self, source_config: Dict[str, Any]):
        src_id = source_config.get("id")
        config = source_config.get("config", {})
        url = config.get("url")
        
        # Configuracion de Storage
        storage_config = source_config.get("storage", {})
        bucket_name = storage_config.get("bucket", "raw-data")
        
        # Generar path historico por defecto: web/{id}/YYYY-MM-DD_HHMMSS.html
        now = datetime.now()
        timestamp_path = now.strftime("%Y-%m-%d_%H%M%S")
        default_path = f"web/{src_id}/{timestamp_path}.html"
        
        remote_path = storage_config.get("path", default_path)
        
        if not url:
            logger.error(f"[WebScraperExtractor] Falta URL en config de {src_id}")
            return

        logger.info(f"[WebScraperExtractor] Descargando HTML de {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Subir a Supabase Storage
            client = BackendClient()
            client.upload_file(
                bucket_name=bucket_name,
                file_path=remote_path,
                file_content=response.content,
                content_type="text/html"
            )
            
        except Exception as e:
            logger.error(f"[WebScraperExtractor] Error extrayendo {src_id}: {e}")
