"""
Transformers específicos por fuente de datos.

Cada fuente con lógica particular tiene su propio transformer aquí.
Esto evita contaminar las clases genéricas (ExcelTransformer, ApiTransformer)
con lógica específica de cada fuente.

Convención:
- Un archivo por fuente: {source_id}.py
- Clase debe heredar de BaseSourceTransformer
- Se registra automáticamente al importar
"""
from .base_source import BaseSourceTransformer, source_transformer_registry

# Auto-registro: importar todos los transformers específicos
# Los transformers se registran al ser importados usando el decorador @register_source_transformer
try:
    from . import minminas_oferta
except ImportError:
    pass

try:
    from . import upme_demanda
except ImportError:
    pass

__all__ = [
    "BaseSourceTransformer",
    "source_transformer_registry",
]
