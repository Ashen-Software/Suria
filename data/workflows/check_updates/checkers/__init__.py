from typing import Dict, Type, Optional
from services.backend_client import BackendClient
from .base import BaseChecker
from .api import ApiChecker
from .web import WebScraperChecker
from .complex import ComplexScraperChecker

# Registro de checkers disponibles mapeados por 'type' en sources_config.json
CHECKER_REGISTRY: Dict[str, Type[BaseChecker]] = {
    "api": ApiChecker,
    "scrape": WebScraperChecker,
    "complex_scraper": ComplexScraperChecker
}

def get_checker(source_type: str, backend_client: BackendClient) -> Optional[BaseChecker]:
    """Factory para obtener el checker adecuado según el tipo de fuente."""
    checker_class = CHECKER_REGISTRY.get(source_type)
    if checker_class:
        return checker_class(backend_client)
    return None
