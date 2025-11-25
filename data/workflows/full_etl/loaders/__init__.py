"""
Loaders para cargar datos transformados a PostgreSQL (Supabase).

Módulos:
- dimension_resolver: Lookups y upserts de dimensiones
- fact_loader: Inserción de tablas de hechos
"""
from .dimension_resolver import DimensionResolver
from .fact_loader import FactLoader

__all__ = ["DimensionResolver", "FactLoader"]
