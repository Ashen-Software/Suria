"""
Funciones y clases comunes para todos los normalizadores.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any, Dict, List, Optional

import pandas as pd

# Mapeo de escenarios para energía eléctrica, potencia máxima y capacidad instalada
# Nota: Estos archivos solo tienen ESC_MEDIO e intervalos de confianza
# Los escenarios bajo y alto solo existen en gas natural (ver GAS_SCENARIO_MAP)
SCENARIO_MAP = {
    "esc. medio": "ESC_MEDIO",
    "esc medio": "ESC_MEDIO",
    "escenario medio": "ESC_MEDIO",
    "ic superior 95": "IC_SUP_95",
    "ic inferior 95": "IC_INF_95",
    "ic superior 68": "IC_SUP_68",
    "ic inferior 68": "IC_INF_68",
}

MONTH_MAP = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "set": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}


@dataclass
class ColumnMetadata:
    scenario: str
    descriptor: str
    unit: str


@dataclass
class NormalizedRecord:
    period_key: str
    periodicidad: str
    metric: str
    unidad: str
    ambito: str
    descriptor: str
    escenario: str
    valor: float
    revision: str
    year_span: str
    sheet_name: str
    source_file: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "period_key": self.period_key,
            "periodicidad": self.periodicidad,
            "metric": self.metric,
            "unidad": self.unidad,
            "ambito": self.ambito,
            "descriptor": self.descriptor,
            "escenario": self.escenario,
            "valor": self.valor,
            "revision": self.revision,
            "year_span": self.year_span,
            "sheet_name": self.sheet_name,
            "source_file": self.source_file,
        }


def drop_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina columnas completamente vacías."""
    keep_cols = [col for col in df.columns if not df[col].isna().all()]
    return df[keep_cols]


def flatten_column(col: Any) -> str:
    """Aplana una columna multi-nivel a string."""
    if isinstance(col, tuple):
        parts = [str(part).strip() for part in col if str(part).strip() not in {"", "nan"}]
        return " ".join(parts)
    return str(col).strip()


def find_period_column(columns: List[str]) -> Optional[int]:
    """Encuentra el índice de la columna de período."""
    for idx, col in enumerate(columns):
        lower = col.lower()
        if "periodo" in lower or "año" in lower or "ano" in lower or "mes" in lower:
            return idx
    return 0 if columns else None


def parse_column_metadata(label: str, default_unit: str) -> Optional[ColumnMetadata]:
    """Parsea los metadatos de una columna (escenario, descriptor, unidad)."""
    normalized = normalize_spaces(label)
    lowered = normalized.lower()
    scenario = None
    for key, value in SCENARIO_MAP.items():
        if key in lowered:
            scenario = value
            lowered = lowered.replace(key, "")
            normalized = normalized.replace(key, "")
    if scenario is None:
        scenario = "ESC_MEDIO"

    unit_match = re.search(r"\(([^)]+)\)", normalized)
    unit_value = unit_match.group(1) if unit_match else default_unit
    descriptor = normalized
    if unit_match:
        descriptor = normalized.replace(unit_match.group(0), "").strip()
    descriptor = descriptor.replace("Esc.", "").strip()
    if not descriptor:
        return None

    return ColumnMetadata(
        scenario=scenario,
        descriptor=descriptor,
        unit=unit_value.strip(),
    )


def normalize_spaces(value: str) -> str:
    """Normaliza espacios múltiples a uno solo."""
    return re.sub(r"\s+", " ", value or "").strip()


def build_period_key(value: Any, periodicity: str) -> Optional[str]:
    """Construye una clave de período en formato YYYY-MM-DD."""
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        dt = value.to_pydatetime()
        if periodicity == "mensual":
            return dt.strftime("%Y-%m-01")
        return dt.strftime("%Y-01-01")
    if isinstance(value, datetime):
        if periodicity == "mensual":
            return value.strftime("%Y-%m-01")
        return value.strftime("%Y-01-01")

    text = str(value).strip().lower()
    if periodicity == "anual":
        match = re.search(r"(\d{4})", text)
        if match:
            return f"{match.group(1)}-01-01"
        if len(text) == 4 and text.isdigit():
            return f"{text}-01-01"
        return None

    # periodicidad mensual
    match = re.match(r"([a-z]{3})[-/ ]?(\d{2,4})", text)
    if match:
        month_txt, year_txt = match.groups()
        month = MONTH_MAP.get(month_txt[:3])
        if month is None:
            return None
        year = int(year_txt) + 2000 if len(year_txt) == 2 else int(year_txt)
        return f"{year:04d}-{month:02d}-01"

    return None


def infer_revision_from_name(name: str) -> str:
    """Infiere la revisión desde el nombre del archivo."""
    lowered = name.lower()
    if "jul" in lowered:
        return "REV_JULIO"
    if "dic" in lowered:
        return "REV_DICIEMBRE"
    if "ene" in lowered:
        return "REV_ENERO"
    return "REV_DESCONOCIDA"


def infer_year_span(name: str) -> str:
    """Infiere el rango de años desde el nombre del archivo."""
    match = re.search(r"(20\d{2})[^\d]+(20\d{2})", name)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    match = re.search(r"(20\d{2})", name)
    if match:
        return match.group(1)
    return "sin_rango"


def fallback_descriptor_for_spec(spec: Dict[str, str], sheet_name: str) -> str:
    """
    Devuelve un descriptor genérico cuando el encabezado viene como 'Unnamed'.
    """
    scope = spec.get("scope_family", "")
    metric = spec.get("metric", "")

    # Total nacional de energía/potencia
    if scope == "nacional":
        return "SIN"

    # Combinaciones SIN + GCE + ME + GD
    if scope == "combinado":
        if metric == "energia":
            return "SIN_GCE_ME_GD"
        if metric == "potencia":
            return "SIN_GCE_ME_GD"

    # Áreas del SIN
    if scope == "area_sin":
        return "AREA_SIN_TOTAL"

    # Generación distribuida
    if scope == "gd":
        return "GD_TOTAL"

    # Fallback
    return "TOTAL"

