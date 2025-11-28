"""
Normalizador principal para Series Históricas de Demanda de Gas Natural UPME.

Este módulo procesa los archivos Excel de gas natural y los normaliza en CSV
unificados por categoría.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# Permite usar el módulo tanto como paquete como script directo
try:
    from .config_gas import (
        GAS_NATURAL_EXCEL_FILES,
        CATEGORIA_MAP,
        PROCESSED_GAS_DIR,
    )
    from .normalizers.gas_natural import normalize_gas_natural_excel
except ImportError:
    from config_gas import (
        GAS_NATURAL_EXCEL_FILES,
        CATEGORIA_MAP,
        PROCESSED_GAS_DIR,
    )
    from normalizers.gas_natural import normalize_gas_natural_excel


def normalize_gas_directory(
    revision_label: Optional[str] = None,
) -> List[Path]:
    """
    Normaliza los archivos de Series Históricas de Gas Natural.
    
    Los CSV se guardan en processed/gas-natural/ con un archivo por categoría.
    """
    PROCESSED_GAS_DIR.mkdir(parents=True, exist_ok=True)
    
    created_files: List[Path] = []
    
    excel_files = [p for p in GAS_NATURAL_EXCEL_FILES if p.exists()]
    missing = [p for p in GAS_NATURAL_EXCEL_FILES if not p.exists()]

    print(f"[normalizer_gas] Archivos configurados: {len(GAS_NATURAL_EXCEL_FILES)}")
    for f in GAS_NATURAL_EXCEL_FILES:
        status = "OK" if f.exists() else "NO_ENCONTRADO"
        print(f"  - {f.name} [{status}]")

    if not excel_files:
        print("[normalizer_gas] Ninguno de los archivos configurados existe. Nada que normalizar.")
        return created_files

    print(f"[normalizer_gas] Archivos a procesar: {len(excel_files)}")

    # Consolidar todos los registros en una sola lista
    all_records: List[Dict] = []

    for file_path in excel_files:
        print(f"\n[normalizer_gas] Procesando: {file_path.name}")
        try:
            payload = normalize_gas_natural_excel(
                file_path,
                CATEGORIA_MAP,
                revision_label
            )
            records = payload["records"]
            
            if not records:
                print(f"[normalizer_gas] No se encontraron registros en {file_path.name}")
                continue

            # Agregar todos los registros a la lista consolidada
            all_records.extend(records)
            
            print(f"[normalizer_gas] Procesados {len(records)} registros")
            
        except Exception as e:
            print(f"[normalizer_gas] Error procesando {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Guardar un solo CSV consolidado con todos los datos
    if all_records:
        output_path = PROCESSED_GAS_DIR / "gas_natural_consolidado_normalized.csv"
        
        df = pd.DataFrame(all_records)
        df.to_csv(output_path, index=False, encoding="utf-8")
        created_files.append(output_path)
        
        # Mostrar estadísticas por categoría y escenario
        total = len(all_records)
        categorias = {}
        escenarios = {}
        for r in all_records:
            cat = r.get("categoria", "UNKNOWN")
            esc = r.get("escenario", "unknown")
            categorias[cat] = categorias.get(cat, 0) + 1
            escenarios[esc] = escenarios.get(esc, 0) + 1
        
        print(f"\n[normalizer_gas] Guardado: {output_path.name}")
        print(f"[normalizer_gas] Total de registros: {total}")
        print(f"[normalizer_gas] Por categoría:")
        for cat, count in sorted(categorias.items()):
            print(f"  - {cat}: {count}")
        print(f"[normalizer_gas] Por escenario:")
        for esc, count in sorted(escenarios.items()):
            print(f"  - {esc}: {count}")
    else:
        print("[normalizer_gas] No se generaron registros. Nada que guardar.")
    
    return created_files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normaliza archivos de Series Históricas de Gas Natural UPME.")
    parser.add_argument(
        "--revision",
        type=str,
        default=None,
        help="Etiqueta de revisión a forzar (ej: REV_JULIO_2025).",
    )
    args = parser.parse_args()

    files = normalize_gas_directory(args.revision)
    print(f"\n[normalizer_gas] Total de archivos CSV generados: {len(files)}")
    for f in files:
        print(f"  - {f}")

