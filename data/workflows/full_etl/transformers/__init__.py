from typing import Dict, Type, Optional
from .base import BaseTransformer
from .api import ApiTransformer
from .excel import ExcelTransformer
from .custom import CustomTransformer
from .config import get_transformation_config, register_transformation_config, TransformationConfig, ValidationRule
from .data_cleaner import DataValidator

# Import source transformers registry
from .source_transformers import source_transformer_registry, BaseSourceTransformer
from .source_transformers.base_source import get_source_transformer

# Registry por TIPO de fuente (api, scrape, complex_scraper)
TYPE_TRANSFORMER_REGISTRY: Dict[str, Type[BaseTransformer]] = {
    "api": ApiTransformer,
    "scrape": ApiTransformer,
    "web": ApiTransformer,
    "complex_scraper": CustomTransformer,
    "excel": ExcelTransformer,
}

# Alias para compatibilidad
TRANSFORMER_REGISTRY = TYPE_TRANSFORMER_REGISTRY


def get_transformer(
    source_type: str, 
    source_id: Optional[str] = None
) -> Optional[BaseTransformer]:
    """
    Obtiene la instancia del transformer correspondiente.
    
    Prioridad:
    1. Si source_id tiene un transformer específico registrado, usarlo
    2. Sino, usar el transformer genérico por tipo
    
    Args:
        source_type: Tipo de fuente (api, scrape, complex_scraper, excel)
        source_id: Identificador opcional de la fuente específica
        
    Returns:
        Instancia del transformer o None si no existe
    """
    # Primero intentar obtener transformer específico por source_id
    if source_id:
        source_transformer = get_source_transformer(source_id)
        if source_transformer:
            return source_transformer
    
    # Fallback a transformer genérico por tipo
    transformer_class = TYPE_TRANSFORMER_REGISTRY.get(source_type)
    if transformer_class:
        return transformer_class()
    
    return None


def get_transformer_for_source(source_config: Dict) -> Optional[BaseTransformer]:
    """
    Obtiene el transformer apropiado para una configuración de fuente.
    
    Usa source_id para buscar transformer específico, sino usa el tipo.
    
    Args:
        source_config: Configuración completa de la fuente
        
    Returns:
        Instancia del transformer
    """
    source_id = source_config.get("id")
    source_type = source_config.get("type", "api")
    
    return get_transformer(source_type, source_id)
