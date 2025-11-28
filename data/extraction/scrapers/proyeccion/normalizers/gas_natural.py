"""
Normalizador específico para Series Históricas de Demanda de Gas Natural.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

import pandas as pd

from .common import (
    build_period_key,
    infer_revision_from_name,
    infer_year_span,
    normalize_spaces,
)

# Mapeo de escenarios para gas natural
GAS_SCENARIO_MAP = {
    "esc. bajo": "ESC_BAJO",
    "esc bajo": "ESC_BAJO",
    "escenario bajo": "ESC_BAJO",
    "esc. medio": "ESC_MEDIO",
    "esc medio": "ESC_MEDIO",
    "histórico / esc. medio": "ESC_MEDIO",
    "historico / esc medio": "ESC_MEDIO",
    "esc. alto": "ESC_ALTO",
    "esc alto": "ESC_ALTO",
    "escenario alto": "ESC_ALTO",
}


@dataclass
class GasNaturalRecord:
    """Registro normalizado para demanda de gas natural."""
    period_key: str
    periodicidad: str
    categoria: str
    region: Optional[str]
    nodo: Optional[str]
    escenario: str
    valor: float
    unidad: str
    revision: str
    year_span: str
    sheet_name: str
    source_file: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "period_key": self.period_key,
            "periodicidad": self.periodicidad,
            "categoria": self.categoria,
            "region": self.region,
            "nodo": self.nodo,
            "escenario": self.escenario,
            "valor": self.valor,
            "unidad": self.unidad,
            "revision": self.revision,
            "year_span": self.year_span,
            "sheet_name": self.sheet_name,
            "source_file": self.source_file,
        }


def extract_categoria_from_filename(filename: str, categoria_map: Dict[str, str]) -> Optional[str]:
    """Extrae la categoría del nombre del archivo."""
    filename_lower = filename.lower()
    for key, value in categoria_map.items():
        if key in filename_lower:
            return value
    return None


def parse_gas_scenario(sheet_name: str) -> str:
    """Parsea el escenario desde el nombre de la hoja."""
    normalized = normalize_spaces(sheet_name.lower())
    for key, value in GAS_SCENARIO_MAP.items():
        if key in normalized:
            return value
    return "ESC_MEDIO"  # Default


def find_date_column(df: pd.DataFrame) -> Optional[int]:
    """Encuentra la columna que contiene fechas/períodos."""
    for idx, col in enumerate(df.columns):
        col_str = str(col).lower()
        # Buscar columnas que puedan contener fechas
        if any(keyword in col_str for keyword in ["fecha", "periodo", "mes", "año", "ano", "date"]):
            return idx
        # Si la primera columna tiene valores que parecen fechas (mmm-yy)
        if idx == 0:
            sample = df.iloc[0, idx] if len(df) > 0 else None
            if sample and isinstance(sample, str):
                if re.match(r"[a-z]{3}[-/ ]?\d{2}", sample.lower()):
                    return idx
    return 0  # Default: primera columna


def normalize_gas_natural_excel(
    file_path: Path,
    categoria_map: Dict[str, str],
    revision_label: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Normaliza un archivo Excel de Series Históricas de Gas Natural.
    
    Args:
        file_path: Ruta del archivo Excel
        categoria_map: Mapa de categorías desde nombres de archivo
        revision_label: Etiqueta de revisión opcional
        
    Returns:
        Dict con metadata y registros normalizados
    """
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))

    revision = revision_label or infer_revision_from_name(file_path.name)
    year_span = infer_year_span(file_path.name)
    categoria = extract_categoria_from_filename(file_path.name, categoria_map)
    
    if not categoria:
        raise ValueError(f"No se pudo extraer la categoría del archivo: {file_path.name}")

    excel = pd.ExcelFile(file_path)
    records: List[GasNaturalRecord] = []

    for sheet_name in excel.sheet_names:
        try:
            # Intentar leer con header multi-nivel primero
            df = excel.parse(sheet_name, header=[0, 1])
        except (ValueError, IndexError):
            try:
                df = excel.parse(sheet_name, header=0)
            except Exception as e:
                print(f"[gas_natural] Error leyendo hoja {sheet_name}: {e}")
                continue

        if df.empty:
            continue

        # Determinar escenario desde el nombre de la hoja
        sheet_escenario = parse_gas_scenario(sheet_name)
        
        # Si la hoja tiene header multi-nivel, buscar información de región en las primeras filas
        # Esto es común en hojas como "Esc Med Regional" donde la primera fila tiene "Región"
        region_header_map: Dict[int, str] = {}  # Mapeo col_idx -> región
        if isinstance(df.columns[0], tuple):
            # Buscar en las primeras filas si hay información de región
            for i in range(min(5, len(df))):
                first_cell = df.iloc[i, 0] if len(df.columns) > 0 else None
                if first_cell and isinstance(first_cell, str):
                    first_lower = first_cell.lower()
                    if "región" in first_lower or "region" in first_lower or "nodo" in first_lower:
                        # Esta fila tiene headers de región/nodo, mapear columnas
                        for j in range(1, len(df.columns)):
                            cell_val = df.iloc[i, j] if i < len(df) else None
                            if cell_val and isinstance(cell_val, str):
                                cell_clean = str(cell_val).strip()
                                if cell_clean and cell_clean not in ["-", ""]:
                                    region_header_map[j] = cell_clean
                        break

        # Encontrar columna de fechas
        date_col_idx = find_date_column(df)
        if date_col_idx is None:
            # Intentar usar la primera columna si parece tener fechas
            if len(df) > 0:
                first_val = df.iloc[0, 0]
                if isinstance(first_val, str) and re.match(r"[a-z]{3}[-/ ]?\d{2}", first_val.lower()):
                    date_col_idx = 0
                else:
                    continue
            else:
                continue

        # Obtener fechas (saltar filas de header si existen)
        start_row = 0
        # Buscar la primera fila que tenga una fecha válida
        for i in range(min(10, len(df))):
            val = df.iloc[i, date_col_idx]
            if pd.notna(val) and isinstance(val, str):
                if re.match(r"[a-z]{3}[-/ ]?\d{2}", val.lower()):
                    start_row = i
                    break
        
        date_series = df.iloc[start_row:, date_col_idx].reset_index(drop=True)
        
        # Procesar columnas de datos (todas excepto la de fechas)
        for col_idx in range(len(df.columns)):
            if col_idx == date_col_idx:
                continue

            col_name = df.columns[col_idx]
            # Aplanar nombre de columna si es multi-nivel
            if isinstance(col_name, tuple):
                # Extraer partes no vacías y no "Unnamed"
                parts = []
                for c in col_name:
                    c_str = str(c).strip()
                    if c_str and c_str.lower() not in {"", "nan", "unnamed"}:
                        # Si contiene "unnamed" pero tiene números, puede ser un índice
                        if "unnamed" in c_str.lower():
                            # Buscar en la fila de datos si hay información útil
                            continue
                        parts.append(c_str)
                col_label = " ".join(parts) if parts else ""
            else:
                col_label = str(col_name).strip()

            # Si la columna tiene "Unnamed", intentar extraer el nombre real
            if not col_label or "unnamed" in col_label.lower():
                # Primero, verificar si tenemos un mapeo de región desde el header
                if col_idx in region_header_map:
                    col_label = region_header_map[col_idx]
                else:
                    # Buscar en las primeras filas de datos si hay un nombre útil
                    for i in range(start_row, min(start_row + 5, len(df))):
                        cell_val = df.iloc[i, col_idx] if i < len(df) else None
                        if cell_val and isinstance(cell_val, str):
                            cell_clean = str(cell_val).strip()
                            # Si parece un nombre de región o nodo, usarlo
                            if cell_clean and cell_clean not in ["-", ""]:
                                if cell_clean.upper() in ["CENTRO", "COSTA ATLÁNTICA", "COSTA INTERIOR", "CQR", 
                                                         "MAGDALENA MEDIO", "NOROCCIDENTE", "NORORIENTE", 
                                                         "SUROCCIDENTE", "TOLIMA-HUILA", "NACIONAL"]:
                                    col_label = cell_clean
                                    break
                                elif " - (" in cell_clean or len(cell_clean.split()) > 2:
                                    col_label = cell_clean
                                    break
                
                # Si aún no tenemos label, intentar usar el índice de columna como fallback
                if not col_label or "unnamed" in col_label.lower():
                    # Último recurso: usar el índice de columna (solo si realmente no hay otra opción)
                    # Pero mejor saltar esta columna si no podemos identificar qué es
                    continue
            
            # Limpiar etiquetas de unidad y escenario del nombre de columna
            col_label_clean = col_label
            # Remover unidades entre corchetes
            col_label_clean = re.sub(r'\[.*?\]', '', col_label_clean).strip()
            # Remover referencias a escenarios del nombre de columna (el escenario viene de la hoja)
            for esc_key in ["esc. bajo", "esc bajo", "escenario bajo", "esc. medio", "esc medio", 
                           "escenario medio", "esc. alto", "esc alto", "escenario alto"]:
                col_label_clean = re.sub(esc_key, '', col_label_clean, flags=re.IGNORECASE).strip()
            col_label_clean = normalize_spaces(col_label_clean)

            # Si después de limpiar queda vacío, saltar
            if not col_label_clean:
                continue

            # Determinar si es región o nodo
            region = None
            nodo = None
            
            # Si el nombre contiene información de región/nodo, extraerla
            if " - (" in col_label_clean:
                # Formato: "NODO - (SISTEMA)"
                parts = col_label_clean.split(" - (")
                nodo = parts[0].strip() if parts else None
            elif col_label_clean.upper() in ["CENTRO", "COSTA ATLÁNTICA", "COSTA INTERIOR", "CQR", 
                                       "MAGDALENA MEDIO", "NOROCCIDENTE", "NORORIENTE", 
                                       "SUROCCIDENTE", "TOLIMA-HUILA", "TOLIMA HUILA", "NACIONAL"]:
                region = col_label_clean.upper()
            else:
                # Intentar determinar si es región o nodo
                # Si tiene paréntesis o es muy largo, probablemente es un nodo
                if "(" in col_label_clean or len(col_label_clean.split()) > 3:
                    nodo = col_label_clean
                else:
                    region = col_label_clean.upper()
            
            # Si tenemos región del header y no encontramos región/nodo, usar la del header
            if col_idx in region_header_map and not region and not nodo:
                # Intentar determinar si el valor del header es región o nodo
                header_val = region_header_map[col_idx]
                if header_val.upper() in ["CENTRO", "COSTA ATLÁNTICA", "COSTA INTERIOR", "CQR", 
                                         "MAGDALENA MEDIO", "NOROCCIDENTE", "NORORIENTE", 
                                         "SUROCCIDENTE", "TOLIMA-HUILA", "NACIONAL"]:
                    region = header_val.upper()
                else:
                    nodo = header_val

            # Usar escenario de la hoja, no de la columna
            escenario = sheet_escenario

            # Procesar valores (desde start_row)
            value_series = df.iloc[start_row:, col_idx].reset_index(drop=True)
            
            for date_value, raw_value in zip(date_series, value_series):
                if pd.isna(date_value):
                    continue

                # Convertir valor a número
                numeric_value = pd.to_numeric(raw_value, errors="coerce")
                if pd.isna(numeric_value) or numeric_value == 0:
                    continue

                # Construir period_key (siempre mensual para gas natural)
                period_key = build_period_key(date_value, "mensual")
                if period_key is None:
                    continue

                record = GasNaturalRecord(
                    period_key=period_key,
                    periodicidad="mensual",
                    categoria=categoria,
                    region=region,
                    nodo=nodo,
                    escenario=escenario,
                    valor=float(numeric_value),
                    unidad="GBTUD",
                    revision=revision,
                    year_span=year_span,
                    sheet_name=sheet_name,
                    source_file=file_path.name,
                )
                records.append(record)

    metadata = {
        "source": str(file_path),
        "categoria": categoria,
        "revision": revision,
        "year_span": year_span,
        "total_records": len(records),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    return {
        "metadata": metadata,
        "records": [r.to_dict() for r in records],
    }

