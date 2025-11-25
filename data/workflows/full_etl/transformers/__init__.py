from typing import Dict, Type, Optional
from .base import BaseTransformer
from .api import ApiTransformer
from .excel import ExcelTransformer
from .custom import CustomTransformer

TRANSFORMER_REGISTRY: Dict[str, Type[BaseTransformer]] = {
    "api": ApiTransformer,
    "scrape": ApiTransformer,
    "complex_scraper": CustomTransformer
}

def get_transformer(source_type: str) -> Optional[BaseTransformer]:
    """
    Obtiene la instancia del transformer correspondiente al tipo de fuente.
    
    Args:
        source_type: Tipo de fuente (api, scrape, complex_scraper)
        
    Returns:
        Instancia del transformer o None si no existe
    """
    transformer_class = TRANSFORMER_REGISTRY.get(source_type)
    if transformer_class:
        return transformer_class()
    return None
