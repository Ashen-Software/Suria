"""
Normalizador principal para los anexos Excel de proyección de demanda eléctrica UPME.

Este módulo orquesta la normalización usando los normalizadores específicos
por tipo de métrica (energía eléctrica, potencia máxima, capacidad instalada).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Permite usar el módulo tanto como paquete (`python -m ...proyeccion.normalizer`)
# como script directo (`python normalizer.py`).
try:  # tipo: ignore[block-except]
    from .config import (
        HARDCODED_EXCEL_FILES,
        PROCESSED_DIR,
        PROCESSED_ENERGIA_DIR,
        PROCESSED_POTENCIA_DIR,
        PROCESSED_CAPACIDAD_DIR,
    )  # type: ignore[import]
    from .normalizers import (
        normalize_energia_electrica,
        normalize_potencia_maxima,
        normalize_capacidad_instalada,
        infer_revision_from_name,
        infer_year_span,
    )  # type: ignore[import]
except ImportError:  # ejecución directa
    from config import (
        HARDCODED_EXCEL_FILES,
        PROCESSED_DIR,
        PROCESSED_ENERGIA_DIR,
        PROCESSED_POTENCIA_DIR,
        PROCESSED_CAPACIDAD_DIR,
    )  # type: ignore[no-redef]
    from normalizers import (
        normalize_energia_electrica,
        normalize_potencia_maxima,
        normalize_capacidad_instalada,
        infer_revision_from_name,
        infer_year_span,
    )  # type: ignore[no-redef]


def normalize_excel(file_path: Path, revision_label: Optional[str] = None) -> Dict[str, Any]:
    """
    Normaliza un archivo Excel usando los normalizadores modulares por métrica.
    
    Retorna metadata + registros planos organizados por tipo de métrica.
    """
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))

    revision = revision_label or infer_revision_from_name(file_path.name)
    year_span = infer_year_span(file_path.name)

    excel = pd.ExcelFile(file_path)
    
    # Normalizar usando los módulos específicos por métrica
    energia_records = normalize_energia_electrica(excel, file_path, revision, year_span)
    potencia_records = normalize_potencia_maxima(excel, file_path, revision, year_span)
    capacidad_records = normalize_capacidad_instalada(excel, file_path, revision, year_span)
    
    # Combinar todos los registros
    all_records = energia_records + potencia_records + capacidad_records

    metadata = {
        "source": str(file_path),
        "revision": revision,
        "year_span": year_span,
        "total_records": len(all_records),
        "records_by_metric": {
            "energia": len(energia_records),
            "potencia": len(potencia_records),
            "capacidad": len(capacidad_records),
        },
        # Fecha en UTC con zona horaria explícita para evitar warnings
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    payload = {
        "metadata": metadata,
        "records": [r.to_dict() for r in all_records],
    }
    return payload


def get_output_dir_for_metric(metric: str) -> Path:
    """
    Retorna el directorio de salida según el tipo de métrica.
    """
    metric_lower = metric.lower()
    if "energia" in metric_lower or "energía" in metric_lower:
        return PROCESSED_ENERGIA_DIR
    elif "potencia" in metric_lower:
        return PROCESSED_POTENCIA_DIR
    elif "capacidad" in metric_lower:
        return PROCESSED_CAPACIDAD_DIR
    else:
        # Fallback: guardar en el directorio base de processed
        return PROCESSED_DIR


def normalize_directory(
    output_base_dir: Optional[Path] = None,
    revision_label: Optional[str] = None,
) -> List[Path]:
    """
    Normaliza los anexos definidos en config.HARDCODED_EXCEL_FILES.
    
    Los CSV se guardan en subcarpetas según la métrica:
    - energia-electrica/ para métricas de energía
    - potencia-maxima/ para métricas de potencia
    - capacidad-instalada/ para métricas de capacidad
    """
    # Asegurar que los directorios de salida existan
    PROCESSED_ENERGIA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_POTENCIA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_CAPACIDAD_DIR.mkdir(parents=True, exist_ok=True)
    
    created_files: List[Path] = []

    excel_files = [p for p in HARDCODED_EXCEL_FILES if p.exists()]
    missing = [p for p in HARDCODED_EXCEL_FILES if not p.exists()]

    print(f"[normalizer] Archivos configurados: {len(HARDCODED_EXCEL_FILES)}")
    for f in HARDCODED_EXCEL_FILES:
        status = "OK" if f.exists() else "NO_ENCONTRADO"
        print(f"  - {f} [{status}]")

    if not excel_files:
        print("[normalizer] Ninguno de los archivos configurados existe. Nada que normalizar.")
        return created_files

    print(f"[normalizer] Archivos a procesar: {len(excel_files)}")

    for file_path in excel_files:
        print(f"\n[normalizer] Procesando: {file_path.name}")
        payload = normalize_excel(file_path, revision_label)
        records = payload["records"]
        
        if not records:
            print(f"[normalizer] No se encontraron registros en {file_path.name}")
            continue
        
        # Mostrar estadísticas por métrica
        metadata = payload["metadata"]
        if "records_by_metric" in metadata:
            print(f"[normalizer] Registros por métrica:")
            for metric, count in metadata["records_by_metric"].items():
                if count > 0:
                    print(f"  - {metric}: {count}")
        
        # Separar registros solo por métrica (mensuales y anuales juntos)
        records_by_metric: Dict[str, List[Dict[str, Any]]] = {}
        for record in records:
            metric = record.get("metric", "unknown")
            if metric not in records_by_metric:
                records_by_metric[metric] = []
            records_by_metric[metric].append(record)
        
        # Guardar un CSV por cada métrica encontrada (incluye mensuales y anuales)
        for metric, metric_records in records_by_metric.items():
            output_dir = get_output_dir_for_metric(metric)
            output_path = output_dir / f"{file_path.stem}_{metric}_normalized.csv"
            
            df = pd.DataFrame(metric_records)
            df.to_csv(output_path, index=False, encoding="utf-8")
            created_files.append(output_path)
            
            # Mostrar desglose por periodicidad
            periodicidades = {}
            for r in metric_records:
                p = r.get("periodicidad", "unknown")
                periodicidades[p] = periodicidades.get(p, 0) + 1
            
            period_str = ", ".join([f"{k}: {v}" for k, v in periodicidades.items()])
            print(f"[normalizer] Guardado: {output_path.name} ({len(metric_records)} registros - {period_str})")
    
    return created_files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normaliza anexos de proyección UPME (rutas quemadas).")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directorio base para escribir los CSV normalizados (por defecto usa processed/ con subcarpetas por métrica).",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default=None,
        help="Etiqueta de revisión a forzar (ej: REV_JULIO_2025).",
    )
    args = parser.parse_args()

    files = normalize_directory(args.output_dir, args.revision)
    print(f"\n[normalizer] Total de archivos CSV generados: {len(files)}")
    for f in files:
        print(f"  - {f}")
