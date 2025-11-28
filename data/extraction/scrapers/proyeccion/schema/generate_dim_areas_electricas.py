"""
Script para generar INSERTs SQL para dim_areas_electricas
a partir de los CSVs normalizados.

Este script:
1. Lee todos los CSVs normalizados (energía, potencia, capacidad)
2. Extrae valores únicos de (ambito, descriptor)
3. Genera nombres legibles basados en los códigos
4. Genera INSERTs SQL con ON CONFLICT para evitar duplicados
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Set, Tuple

# Mapeo de códigos a nombres legibles
NOMBRE_MAP: Dict[str, str] = {
    "SIN": "Sistema Interconectado Nacional",
    "SIN_GCE_ME": "SIN con GCE, ME",
    "SIN_GCE_ME_GD": "SIN con GCE, ME y Generación Distribuida",
    "SIN_GCE_ME_GD_UPME": "SIN con GCE, ME y GD (UPME)",
    "SIN_GCE_ME_GD_PNUMA": "SIN con GCE, ME y GD (PNUMA)",
    "AREA_SIN_TOTAL": "Total Áreas SIN",
    "CARIBE": "Área Caribe",
    "ORIENTE": "Área Oriente",
    "SUR": "Área Sur",
    "NORDESTE": "Área Nordeste",
    "ANTIOQUIA": "Área Antioquia",
    "VALLE": "Área Valle",
    "CUNDINAMARCA": "Área Cundinamarca",
    "GD_UPME": "Generación Distribuida (UPME)",
    "GD_PNUMA": "Generación Distribuida (PNUMA)",
    "GD": "Generación Distribuida",
    "GD_TOTAL": "Total Generación Distribuida",
}

# Directorio base donde están los CSVs procesados
# Calcular ruta desde el archivo actual hasta la raíz del proyecto
# __file__ está en: data/extraction/scrapers/proyeccion/schema/generate_dim_areas_electricas.py
# Necesitamos llegar a: frontend/public/data/extraction/scrapers/proyeccion/processed
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "extraction" / "scrapers" / "proyeccion" / "processed"
FRONTEND_PUBLIC_DIR = PROJECT_ROOT / "frontend" / "public" / "data" / "extraction" / "scrapers" / "proyeccion" / "processed"


def generate_readable_name(codigo: str) -> str:
    """Genera un nombre legible a partir de un código."""
    # Si ya existe en el mapa, usarlo
    if codigo in NOMBRE_MAP:
        return NOMBRE_MAP[codigo]
    
    # Si contiene guiones bajos, reemplazarlos y capitalizar
    nombre = codigo.replace("_", " ").title()
    
    # Mejoras específicas
    if "SIN" in nombre:
        nombre = nombre.replace("Sin", "SIN")
    if "GD" in nombre:
        nombre = nombre.replace("Gd", "GD")
    if "GCE" in nombre:
        nombre = nombre.replace("Gce", "GCE")
    if "ME" in nombre and "ME" not in codigo:
        # Evitar reemplazar "ME" si es parte de una palabra
        pass
    
    return nombre


def extract_unique_areas(csv_dir: Path) -> Set[Tuple[str, str]]:
    """
    Extrae valores únicos de (ambito, descriptor) de todos los CSVs normalizados.
    
    Returns:
        Set de tuplas (ambito, descriptor)
    """
    areas: Set[Tuple[str, str]] = set()
    
    # Directorios a procesar (excluyendo gas natural)
    subdirs = ["energia-electrica", "potencia-maxima", "capacidad-instalada"]
    
    for subdir in subdirs:
        subdir_path = csv_dir / subdir
        if not subdir_path.exists():
            print(f"⚠️  Directorio no encontrado: {subdir_path}")
            continue
        
        csv_files = list(subdir_path.glob("*.csv"))
        print(f"📁 Procesando {len(csv_files)} archivos en {subdir}/")
        
        for csv_file in csv_files:
            try:
                with open(csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        ambito = row.get("ambito", "").strip()
                        descriptor = row.get("descriptor", "").strip()
                        
                        if ambito and descriptor:
                            areas.add((ambito, descriptor))
            except Exception as e:
                print(f"  ⚠️  Error leyendo {csv_file.name}: {e}")
    
    return areas


def generate_sql_inserts(areas: Set[Tuple[str, str]]) -> str:
    """
    Genera los INSERTs SQL para dim_areas_electricas.
    
    Args:
        areas: Set de tuplas (ambito, descriptor)
        
    Returns:
        String con los INSERTs SQL
    """
    sql_lines = [
        "-- INSERTs para dim_areas_electricas",
        "-- Generado automáticamente a partir de CSVs normalizados",
        "--",
        "-- Uso: Ejecutar estos INSERTs después de crear la tabla",
        "-- Los INSERTs usan ON CONFLICT para evitar duplicados",
        "",
    ]
    
    # Ordenar por categoria y luego por codigo para mejor legibilidad
    sorted_areas = sorted(areas, key=lambda x: (x[0], x[1]))
    
    for ambito, descriptor in sorted_areas:
        codigo = descriptor
        nombre = generate_readable_name(descriptor)
        categoria = ambito
        
        # Escapar comillas simples en SQL
        codigo_escaped = codigo.replace("'", "''")
        nombre_escaped = nombre.replace("'", "''")
        
        sql_lines.append(
            f"INSERT INTO public.dim_areas_electricas (codigo, nombre, categoria, descripcion)"
            f"\nVALUES ('{codigo_escaped}', '{nombre_escaped}', '{categoria}', NULL)"
            f"\nON CONFLICT (codigo) DO UPDATE SET"
            f"\n  nombre = EXCLUDED.nombre,"
            f"\n  categoria = EXCLUDED.categoria,"
            f"\n  descripcion = EXCLUDED.descripcion;"
        )
        sql_lines.append("")
    
    return "\n".join(sql_lines)


def main():
    """Función principal."""
    print("🔍 Buscando CSVs normalizados...")
    
    # Intentar primero en frontend/public/data
    csv_dir = FRONTEND_PUBLIC_DIR
    if not csv_dir.exists():
        # Si no existe, intentar en processed/
        csv_dir = PROCESSED_DIR
        if not csv_dir.exists():
            print(f"❌ No se encontró el directorio de CSVs procesados")
            print(f"   Buscado en: {FRONTEND_PUBLIC_DIR}")
            print(f"   Buscado en: {PROCESSED_DIR}")
            return
    
    print(f"✅ Directorio encontrado: {csv_dir}")
    
    # Extraer áreas únicas
    print("\n📊 Extrayendo áreas únicas de los CSVs...")
    areas = extract_unique_areas(csv_dir)
    
    print(f"\n✅ Encontradas {len(areas)} áreas únicas:")
    for ambito, descriptor in sorted(areas, key=lambda x: (x[0], x[1])):
        print(f"   - {descriptor} ({ambito})")
    
    # Generar SQL
    print("\n📝 Generando INSERTs SQL...")
    sql = generate_sql_inserts(areas)
    
    # Guardar en archivo
    output_file = Path(__file__).parent / "insert_dim_areas_electricas.sql"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(sql)
    
    print(f"\n✅ SQL generado en: {output_file}")
    print(f"   Total de INSERTs: {len(areas)}")


if __name__ == "__main__":
    main()

