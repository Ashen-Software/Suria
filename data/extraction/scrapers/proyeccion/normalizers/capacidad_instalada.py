"""
Normalizador específico para métricas de capacidad instalada.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

from .common import (
    ColumnMetadata,
    NormalizedRecord,
    drop_empty_columns,
    flatten_column,
    find_period_column,
    parse_column_metadata,
    build_period_key,
    fallback_descriptor_for_spec,
)

# Especificaciones de hojas para capacidad instalada
# Hoja: 13 (anual, generación distribuida)
CAPACIDAD_SHEET_SPECS: Dict[int, Dict[str, str]] = {
    13: {"periodicity": "anual", "metric": "capacidad", "unit_default": "MW-año", "scope_family": "gd"},
}


def normalize_capacidad_instalada(
    excel: pd.ExcelFile,
    file_path: Path,
    revision: str,
    year_span: str,
) -> List[NormalizedRecord]:
    """
    Normaliza las hojas de capacidad instalada de un archivo Excel.
    
    Args:
        excel: Archivo Excel abierto
        file_path: Ruta del archivo fuente
        revision: Etiqueta de revisión
        year_span: Rango de años
        
    Returns:
        Lista de registros normalizados de capacidad instalada
    """
    records: List[NormalizedRecord] = []

    for idx, sheet_name in enumerate(excel.sheet_names, start=1):
        spec = CAPACIDAD_SHEET_SPECS.get(idx)
        if not spec:
            continue

        # Los archivos de capacidad instalada solo tienen ESC_MEDIO e intervalos de confianza
        # No se extrae escenario del nombre de la hoja, se usa el de la columna

        try:
            df = excel.parse(sheet_name, header=[0, 1])
        except ValueError:
            df = excel.parse(sheet_name, header=0)
        
        df = drop_empty_columns(df)
        column_labels = [flatten_column(col) for col in df.columns]

        period_idx = find_period_column(column_labels)
        if period_idx is None:
            continue

        period_values = df.iloc[:, period_idx]
        for col_idx, label in enumerate(column_labels):
            if col_idx == period_idx:
                continue
            
            metadata = parse_column_metadata(label, spec["unit_default"])
            if metadata is None:
                continue

            # Limpieza adicional del descriptor cuando los encabezados vienen vacíos
            if "unnamed" in metadata.descriptor.lower():
                metadata.descriptor = fallback_descriptor_for_spec(spec, sheet_name)

            value_series = df.iloc[:, col_idx]
            for period_value, raw_value in zip(period_values, value_series):
                if pd.isna(period_value):
                    continue

                # Intentar convertir el valor a número
                numeric_value = pd.to_numeric(raw_value, errors="coerce")
                if pd.isna(numeric_value):
                    continue

                period_key = build_period_key(period_value, spec["periodicity"])
                if period_key is None:
                    continue

                record = NormalizedRecord(
                    period_key=period_key,
                    periodicidad=spec["periodicity"],
                    metric=spec["metric"],
                    unidad=metadata.unit,
                    ambito=spec["scope_family"],
                    descriptor=metadata.descriptor,
                    escenario=metadata.scenario,
                    valor=float(numeric_value),
                    revision=revision,
                    year_span=year_span,
                    sheet_name=sheet_name,
                    source_file=file_path.name,
                )
                records.append(record)

    return records

