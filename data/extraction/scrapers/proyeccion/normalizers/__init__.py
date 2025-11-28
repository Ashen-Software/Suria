"""
Módulos normalizadores por tipo de métrica.
"""
from .common import (
    ColumnMetadata,
    NormalizedRecord,
    drop_empty_columns,
    flatten_column,
    find_period_column,
    parse_column_metadata,
    normalize_spaces,
    build_period_key,
    infer_revision_from_name,
    infer_year_span,
    fallback_descriptor_for_spec,
    SCENARIO_MAP,
    MONTH_MAP,
)
from .energia_electrica import normalize_energia_electrica
from .potencia_maxima import normalize_potencia_maxima
from .capacidad_instalada import normalize_capacidad_instalada

__all__ = [
    "ColumnMetadata",
    "NormalizedRecord",
    "drop_empty_columns",
    "flatten_column",
    "find_period_column",
    "parse_column_metadata",
    "normalize_spaces",
    "build_period_key",
    "infer_revision_from_name",
    "infer_year_span",
    "fallback_descriptor_for_spec",
    "SCENARIO_MAP",
    "MONTH_MAP",
    "normalize_energia_electrica",
    "normalize_potencia_maxima",
    "normalize_capacidad_instalada",
]

