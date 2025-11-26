"""
Test simple para Transform + Load con datos reales del bucket.

- get_latest_raw_files() para cargar del bucket
- get_transformer() para obtener el transformer
- transform_multiple_files() para transformar
- FactLoader para cargar

Uso:
    python -m workflows.tests.test_transform_load_simple
    python -m workflows.tests.test_transform_load_simple --skip-load  # Solo transform
    python -m workflows.tests.test_transform_load_simple --limit 50   # Limitar registros
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import argparse
from datetime import datetime

from workflows.full_etl.storage import get_latest_raw_files
from workflows.full_etl.transformers import get_transformer
from workflows.full_etl.pipeline import transform_multiple_files, success_percentage
from workflows.full_etl.loaders import FactLoader


# Config mockeada para api_regalias (no depende de ConfigManager)
MOCK_CONFIGS = {
    "api_regalias": {
        "id": "api_regalias",
        "type": "api",
        "name": "API Regalías ANH",
        "storage": {
            "bucket": "raw-data"
        },
        "transform": {
            "fact_table": "fact_regalias"
        }
    }
}


def get_mock_config(source_id: str) -> dict:
    """Retorna config mockeada para el source_id."""
    return MOCK_CONFIGS.get(source_id, {})


def test_transform(source_id: str, source_config: dict, limit: int = None) -> dict:
    """
    Ejecuta la fase Transform igual que el ETL real.
    
    Returns:
        Dict con valid_records, errors, stats
    """
    print("\n" + "="*60)
    print("FASE: TRANSFORM")
    print("="*60)
    
    # 1. Obtener transformer (igual que run.py)
    src_type = source_config.get("type", source_id)
    transformer = get_transformer(src_type)
    
    if not transformer:
        print(f"No hay transformer para tipo '{src_type}'")
        return {}
    
    print(f"✓ Transformer: {transformer.__class__.__name__}")
    
    # 2. Obtener archivos RAW del storage (igual que run.py)
    print(f"\nCargando archivos desde bucket...")
    raw_files = get_latest_raw_files(source_id, source_config)
    
    if not raw_files:
        print(f"No se encontraron archivos RAW para '{source_id}'")
        return {}
    
    print(f"✓ Archivos encontrados: {len(raw_files)}")
    for file_path, content in raw_files:
        print(f"   - {file_path.split('/')[-1]} ({len(content)} bytes)")
    
    # 3. Transformar usando transform_multiple_files (igual que run.py)
    print(f"\nTransformando...")
    transform_result = transform_multiple_files(raw_files, transformer, source_config)
    
    # 4. Mostrar resultados
    valid_count = len(transform_result.get("valid_records", []))
    error_count = len(transform_result.get("errors", []))
    total_raw = transform_result.get("stats", {}).get("total_raw", 0)
    processing_time = transform_result.get("stats", {}).get("processing_time_seconds", 0)
    
    print(f"\nResultado Transform:")
    print(f"   Total RAW: {total_raw}")
    print(f"   Válidos: {valid_count} ({success_percentage(valid_count, total_raw):.1f}%)")
    print(f"   Errores: {error_count} ({success_percentage(error_count, total_raw):.1f}%)")
    print(f"   Tiempo: {processing_time:.2f}s")
    
    # Categorías de error
    error_categories = transform_result.get("stats", {}).get("error_categories", {})
    if error_categories:
        print(f"\n   Categorías de error:")
        for category, count in sorted(error_categories.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"      - {category}: {count}")
    
    # Ejemplo de registro valido
    valid_records = transform_result.get("valid_records", [])
    if valid_records:
        print(f"\n   Ejemplo de registro válido:")
        sample = valid_records[0]
        print(f"      fact_table: {sample.get('fact_table')}")
        data_keys = list(sample.get('data', {}).keys())
        print(f"      data keys: {data_keys[:6]}{'...' if len(data_keys) > 6 else ''}")
        dims = sample.get('dimensions', {})
        if dims:
            print(f"      dimensions: tiempo={dims.get('tiempo')}, territorio={dims.get('territorio')}")
    
    # Aplicar límite si se especifico
    if limit and valid_count > limit:
        transform_result["valid_records"] = valid_records[:limit]
        print(f"\n   Limitado a {limit} registros para Load")
    
    return transform_result


def test_load(transform_result: dict, source_id: str) -> dict:
    """
    Ejecuta la fase Load igual que el ETL real.
    """
    print("\n" + "="*60)
    print("FASE: LOAD")
    print("="*60)
    
    valid_records = transform_result.get("valid_records", [])
    
    if not valid_records:
        print("No hay registros válidos para cargar")
        return {}
    
    # Determinar fact_table (igual que run.py)
    fact_table = valid_records[0].get("fact_table", "unknown")
    print(f"   Destino: {fact_table}")
    print(f"   Registros a cargar: {len(valid_records)}")
    
    if fact_table != "fact_regalias":
        print(f"No hay loader implementado para '{fact_table}'")
        return {}
    
    # Usar FactLoader (igual que run.py)
    loader = FactLoader(batch_size=10000)
    print(f"FactLoader creado (batch_size=10000)")
    
    load_result = loader.load(valid_records, source_id)
    
    # Stats del resolver
    resolver_stats = load_result.get("resolver_stats", {})
    if resolver_stats:
        print(f"\n   Resolver Stats:")
        print(f"      Cache sizes: {resolver_stats.get('cache_sizes', {})}")
        print(f"      Campos creados: {resolver_stats.get('campos_created_range', 'ninguno')}")
        print(f"      Territorios no encontrados: {resolver_stats.get('territorios_not_found', 0)}")
    
    # Errores detallados
    error_details = load_result.get("error_details", [])
    if error_details:
        print(f"\n   Errores ({len(error_details)}):")
        for err in error_details[:5]:
            print(f"      - idx {err.get('index')}: {err.get('error')}")
        if len(error_details) > 5:
            print(f"      ... y {len(error_details) - 5} más")
    
    return load_result


def main():
    parser = argparse.ArgumentParser(description="Test Transform + Load con datos reales")
    parser.add_argument("--source", type=str, default="api_regalias", help="ID de la fuente")
    parser.add_argument("--skip-load", action="store_true", help="Solo ejecutar transform")
    parser.add_argument("--limit", type=int, default=None, help="Limitar registros para Load")
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("TEST: TRANSFORM + LOAD (datos reales)")
    print("="*60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: {args.source}")
    print(f"Limit: {args.limit or 'sin límite'}")
    print(f"Skip load: {args.skip_load}")
    
    # Usar config mockeada (no depende de ConfigManager)
    source_config = get_mock_config(args.source)
    
    if not source_config:
        print(f"\nNo hay config mockeada para '{args.source}'")
        print(f"   Configs disponibles: {list(MOCK_CONFIGS.keys())}")
        return
    
    print(f"Config mockeada: type={source_config.get('type')}")
    
    # Transform
    transform_result = test_transform(args.source, source_config, args.limit)
    
    if not transform_result.get("valid_records"):
        print("\nNo hay registros válidos. Abortando.")
        return
    
    # Load (si no se skip)
    if not args.skip_load:
        test_load(transform_result, args.source)
    else:
        print("\nLoad skipped por --skip-load")
    
    print("\n" + "="*60)
    print("TEST COMPLETADO")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
