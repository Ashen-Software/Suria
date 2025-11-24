from typing import Dict, Any
from .base import BaseExtractor
from extraction.api_clients.api_loader import run_api_loader
from logs_config.logger import app_logger as logger

class ApiExtractor(BaseExtractor):
    def extract(self, source_config: Dict[str, Any]):
        logger.info(f"[ApiExtractor] Iniciando extracción API para {source_config.get('id')}")
        run_api_loader(source_config)
