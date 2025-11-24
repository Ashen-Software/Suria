from typing import Dict, Any
import requests
import os
from .base import BaseExtractor
from logs_config.logger import app_logger as logger

class WebScraperExtractor(BaseExtractor):
    def extract(self, source_config: Dict[str, Any]):
        src_id = source_config.get("id")
        config = source_config.get("config", {})
        url = config.get("url")
        raw_path = source_config.get("storage", {}).get("local_raw_path", "/app/data/raw/")
        
        if not url:
            logger.error(f"[WebScraperExtractor] Falta URL en config de {src_id}")
            return

        logger.info(f"[WebScraperExtractor] Descargando HTML de {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            os.makedirs(raw_path, exist_ok=True)
            file_name = os.path.join(raw_path, f"data_{src_id}.html")
            
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(response.text)
                
            logger.info(f"[WebScraperExtractor] HTML guardado en {file_name}")
            
        except Exception as e:
            logger.error(f"[WebScraperExtractor] Error extrayendo {src_id}: {e}")
