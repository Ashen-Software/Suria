from typing import Dict, Type, Optional
from .base import BaseExtractor
from .api import ApiExtractor
from .web import WebScraperExtractor
from .complex import ComplexScraperExtractor

EXTRACTOR_REGISTRY: Dict[str, Type[BaseExtractor]] = {
    "api": ApiExtractor,
    "scrape": WebScraperExtractor,
    "complex_scraper": ComplexScraperExtractor
}

def get_extractor(source_type: str) -> Optional[BaseExtractor]:
    extractor_class = EXTRACTOR_REGISTRY.get(source_type)
    if extractor_class:
        return extractor_class()
    return None
