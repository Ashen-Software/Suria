from typing import Dict, Any
from .base import BaseExtractor
from extraction.scrapers.scraper_loader import run_scraper_loader
from logs_config.logger import app_logger as logger

class ComplexScraperExtractor(BaseExtractor):
    def extract(self, source_config: Dict[str, Any]):
        src_id = source_config.get("id")
        logger.info(f"[ComplexScraperExtractor] Delegando extracción de {src_id} a script custom")
        
        # Llama al loader con action='extract'
        run_scraper_loader(source_config, action="extract")
