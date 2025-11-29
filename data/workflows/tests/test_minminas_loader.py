"""
Test de integración para el flujo completo de MinMinas: Transform → Load.

Este script:
1. Descarga metadata y archivos Excel del bucket
2. Transforma los Excel usando el transformer de MinMinas
3. Carga los registros transformados en fact_oferta_gas
4. Muestra estadísticas del proceso completo

Uso:
    python -m workflows.tests.test_minminas_loader
    
    # Solo ver qué haría (dry-run)
    python -m workflows.tests.test_minminas_loader --dry-run
    
    # Limitar número de archivos a procesar
    python -m workflows.tests.test_minminas_loader --max-files 5
    
    # Limitar número de registros a cargar
    python -m workflows.tests.test_minminas_loader --max-records 100
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from logs_config.logger import app_logger as logger


def run_transform(source_config: dict, max_files: int = None) -> dict:
    """
    Ejecuta la fase de transformación.
    
    Args:
        source_config: Configuración de la fuente
        max_files: Limitar número de archivos a procesar
        
    Returns:
        Resultado de la transformación
    """
    from workflows.full_etl.storage import get_latest_metadata_and_excel
    from workflows.full_etl.pipeline import transform_excel_batch
    
    print("\n" + "="*70)
    print("FASE 1: TRANSFORMACIÓN")
    print("="*70)
    
    # 1. Descargar archivos del bucket
    print("\nDescargando archivos del bucket...")
    result = get_latest_metadata_and_excel("gas_natural_declaracion", source_config)
    
    if not result:
        print("No se pudieron descargar archivos del bucket")
        return None
    
    metadata, excel_files = result
    
    print(f"Metadata: extraction_date={metadata.get('extraction_date')}")
    print(f"Total declaraciones: {metadata.get('total_declarations', 0)}")
    print(f"Archivos Excel: {len(excel_files)}")
    
    # Limitar archivos si se especifica
    if max_files and len(excel_files) > max_files:
        print(f"Limitando a {max_files} archivos (de {len(excel_files)})")
        limited_files = dict(list(excel_files.items())[:max_files])
        excel_files = limited_files
    
    for filename, content in list(excel_files.items())[:5]:
        size_kb = len(content) / 1024
        print(f"      • {filename} ({size_kb:.1f} KB)")
    if len(excel_files) > 5:
        print(f"      ... y {len(excel_files) - 5} archivos más")
    
    if not excel_files:
        print("No hay archivos Excel para transformar")
        return None
    
    # 2. Ejecutar transformación
    print("\nEjecutando transformación...")
    transform_result = transform_excel_batch(
        metadata=metadata,
        excel_files=excel_files,
        source_config=source_config
    )
    
    # 3. Mostrar resultados
    stats = transform_result.get("stats", {})
    valid_records = transform_result.get("valid_records", [])
    errors = transform_result.get("errors", [])
    resoluciones = transform_result.get("resoluciones", [])
    
    print(f"\nResultados de transformación:")
    print(f"Archivos procesados: {stats.get('total_files', 0)}")
    print(f"Registros válidos: {stats.get('valid', 0)}")
    print(f"Errores: {stats.get('errors', 0)}")
    print(f"Tiempo: {stats.get('processing_time_seconds', 0):.2f}s")
    print(f"Resoluciones extraídas: {len(resoluciones)}")
    
    # Mostrar muestra de datos
    if valid_records:
        print(f"\nMuestra de registros (primeros 5):")
        print("-" * 70)
        print(f"{'Campo':<20} {'Operador':<20} {'Tipo':<12} {'Fecha':<10} {'Valor':>8}")
        print("-" * 70)
        for rec in valid_records[:5]:
            data = rec.get("data", {})
            campo = str(data.get('campo_nombre', ''))[:19]
            operador = str(data.get('operador', ''))[:19]
            tipo = str(data.get('tipo_produccion', ''))[:11]
            fecha = str(data.get('tiempo_fecha', ''))[:10]
            valor = data.get('valor_gbtud', 0)
            print(f"{campo:<20} {operador:<20} {tipo:<12} {fecha:<10} {valor:>8.3f}")
    
    # Mostrar errores si hay
    if errors:
        print(f"\nPrimeros errores ({len(errors)} total):")
        for i, err in enumerate(errors[:3], 1):
            print(f"   [{i}] {err.get('filename', 'N/A')}: {err.get('error', err.get('message', 'Unknown'))}")
    
    return transform_result


def run_load(transform_result: dict, source_id: str, max_records: int = None, dry_run: bool = False) -> dict:
    """
    Ejecuta la fase de carga.
    
    Args:
        transform_result: Resultado de la transformación
        source_id: ID de la fuente
        max_records: Limitar número de registros a cargar
        dry_run: Si True, solo muestra qué haría
        
    Returns:
        Resultado de la carga
    """
    from workflows.full_etl.loaders import FactLoader
    
    print("\n" + "="*70)
    print("FASE 2: CARGA")
    print("="*70)
    
    valid_records = transform_result.get("valid_records", [])
    resoluciones = transform_result.get("resoluciones", [])
    
    if not valid_records:
        print("\nNo hay registros válidos para cargar")
        return None
    
    # Limitar registros si se especifica
    if max_records and len(valid_records) > max_records:
        print(f"\nLimitando a {max_records} registros (de {len(valid_records)})")
        valid_records = valid_records[:max_records]
    else:
        print(f"\nRegistros a cargar: {len(valid_records)}")
    
    if dry_run:
        print("\n[DRY RUN] No se insertarán datos")
        print("   Para ejecutar realmente, omite --dry-run")
        
        # Mostrar análisis de lo que se haría
        fact_tables = {}
        for rec in valid_records:
            table = rec.get("fact_table", "unknown")
            fact_tables[table] = fact_tables.get(table, 0) + 1
        
        print(f"\n   Distribución por tabla:")
        for table, count in fact_tables.items():
            print(f"      - {table}: {count} registros")
        
        print(f"\n   Resoluciones a insertar/actualizar: {len(resoluciones)}")
        for res in resoluciones[:3]:
            print(f"      - Res. {res.get('numero_resolucion')}: "
                  f"{res.get('periodo_desde')} - {res.get('periodo_hasta')}")
        
        return {"status": "dry_run", "records": len(valid_records)}
    
    # Inicializar loader
    print("\nInicializando FactLoader...")
    try:
        loader = FactLoader(batch_size=10000)
        print("FactLoader inicializado")
    except Exception as e:
        print(f"Error inicializando FactLoader: {e}")
        return None
    
    # Pre-cargar resoluciones si hay
    if resoluciones:
        print(f"\nPre-cargando {len(resoluciones)} resoluciones...")
        try:
            # Las resoluciones se manejarán durante la resolución de dimensiones
            # ya que cada registro tiene su resolucion_number
            print(f"Resoluciones disponibles para resolver")
        except Exception as e:
            print(f"Aviso resoluciones: {e}")
    
    # Ejecutar carga
    print(f"\nEjecutando carga de {len(valid_records)} registros...")
    start_time = datetime.now()
    
    try:
        result = loader.load(valid_records, source_id)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\nResultados de carga:")
        print(f"Tiempo: {elapsed:.2f}s")
        print(f"Status: {result.get('status')}")
        
        stats = result.get("stats", {})
        print(f"\nEstadísticas:")
        print(f"- Total procesados: {stats.get('total_processed', 0)}")
        print(f"- Insertados: {stats.get('inserted', 0)}")
        print(f"- Sin tiempo_id: {stats.get('skipped_no_tiempo', 0)}")
        print(f"- Sin campo_id: {stats.get('skipped_no_campo', 0)}")
        print(f"- Errores: {stats.get('errors', 0)}")
        
        resolver_stats = result.get("resolver_stats", {})
        if resolver_stats:
            print(f"\n   Estadísticas del resolver:")
            print(f"   - Tiempo lookups: {resolver_stats.get('tiempo_lookups', 0)} "
                  f"(cache hits: {resolver_stats.get('tiempo_cache_hits', 0)})")
            print(f"   - Territorio lookups: {resolver_stats.get('territorio_lookups', 0)} "
                  f"(cache hits: {resolver_stats.get('territorio_cache_hits', 0)})")
            print(f"   - Campo lookups: {resolver_stats.get('campo_lookups', 0)} "
                  f"(cache hits: {resolver_stats.get('campo_cache_hits', 0)})")
            print(f"   - Campos creados: {resolver_stats.get('campo_inserts', 0)}")
            print(f"   - Resolución lookups: {resolver_stats.get('resolucion_lookups', 0)} "
                  f"(cache hits: {resolver_stats.get('resolucion_cache_hits', 0)})")
            print(f"   - Resoluciones creadas: {resolver_stats.get('resolucion_inserts', 0)}")
        
        # Mostrar errores si hay
        error_details = result.get("error_details", [])
        if error_details:
            print(f"\n   Primeros errores ({len(error_details)} total):")
            for err in error_details[:5]:
                print(f"   - {err}")
        
        return result
        
    except Exception as e:
        print(f"    Error en carga: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_full_test(max_files: int = None, max_records: int = None, dry_run: bool = False):
    """
    Ejecuta el test completo: Transform → Load.
    
    Args:
        max_files: Limitar número de archivos Excel
        max_records: Limitar número de registros a cargar
        dry_run: Si True, solo muestra qué haría
    """
    print("\n" + "="*70)
    print("TEST INTEGRACIÓN: MinMinas → Transform → Load")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Modo: {'DRY RUN' if dry_run else 'EJECUCIÓN REAL'}")
    if max_files:
        print(f"Límite archivos: {max_files}")
    if max_records:
        print(f"Límite registros: {max_records}")
    
    # Configuración de la fuente
    source_config = {
        "id": "gas_natural_declaracion",
        "type": "complex_scraper",
        "name": "Declaraciones de Producción de Gas Natural - MinEnergía",
        "storage": {
            "bucket": "raw-data"
        }
    }
    source_id = source_config["id"]
    
    # FASE 1: Transformación
    transform_result = run_transform(source_config, max_files=max_files)
    
    if not transform_result:
        print("\n" + "="*70)
        print("TEST FALLIDO: Error en transformación")
        print("="*70)
        return False
    
    valid_count = len(transform_result.get("valid_records", []))
    if valid_count == 0:
        print("\n" + "="*70)
        print("TEST COMPLETADO: Sin registros para cargar")
        print("="*70)
        return True
    
    # FASE 2: Carga
    load_result = run_load(
        transform_result, 
        source_id, 
        max_records=max_records, 
        dry_run=dry_run
    )
    
    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    
    transform_stats = transform_result.get("stats", {})
    print(f"\nTransformación:")
    print(f"   - Archivos: {transform_stats.get('total_files', 0)}")
    print(f"   - Registros válidos: {transform_stats.get('valid', 0)}")
    print(f"   - Errores: {transform_stats.get('errors', 0)}")
    
    if load_result and load_result.get("status") != "dry_run":
        load_stats = load_result.get("stats", {})
        print(f"\nCarga:")
        print(f"   - Procesados: {load_stats.get('total_processed', 0)}")
        print(f"   - Insertados: {load_stats.get('inserted', 0)}")
        print(f"   - Errores: {load_stats.get('errors', 0)}")
        
        resolver_stats = load_result.get("resolver_stats", {})
        new_campos = resolver_stats.get("campo_inserts", 0)
        new_resoluciones = resolver_stats.get("resolucion_inserts", 0)
        if new_campos or new_resoluciones:
            print(f"\nNuevas entidades creadas:")
            if new_campos:
                print(f"   - Campos: {new_campos}")
            if new_resoluciones:
                print(f"   - Resoluciones: {new_resoluciones}")
    elif load_result and load_result.get("status") == "dry_run":
        print(f"\nCarga: [DRY RUN] {load_result.get('records', 0)} registros preparados")
    
    print("\n" + "="*70)
    print("TEST COMPLETADO")
    print("="*70 + "\n")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Test de integración MinMinas: Transform → Load"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Solo mostrar qué haría sin insertar datos"
    )
    parser.add_argument(
        "--max-files", "-f",
        type=int,
        default=None,
        help="Limitar número de archivos Excel a procesar"
    )
    parser.add_argument(
        "--max-records", "-r",
        type=int,
        default=None,
        help="Limitar número de registros a cargar"
    )
    
    args = parser.parse_args()
    
    success = run_full_test(
        max_files=args.max_files,
        max_records=args.max_records,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
