"""
Test de integración para el flujo de transformación de MinMinas.

Este script:
1. Descarga metadata y archivos Excel del bucket
2. Transforma los Excel usando el nuevo parser
3. Muestra estadísticas y primeros registros

Uso:
    python -m workflows.tests.test_minminas_transform
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from workflows.full_etl.storage import get_latest_metadata_and_excel
from workflows.full_etl.pipeline import transform_excel_batch
# from services.config_manager import ConfigManager
# from logs_config.logger import app_logger as logger


def test_minminas_transform():
    """Ejecuta test de transformación de MinMinas."""
    
    print("\n" + "="*60)
    print("TEST: Transformación MinMinas Gas Natural Declaración")
    print("="*60 + "\n")
    
    # config_manager = ConfigManager()
    source_config = {
        "id": "gas_natural_declaracion",
        "type": "complex_scraper",
        "name": "Declaraciones de Producción de Gas Natural - MinEnergía",
        "storage": {
            "bucket": "raw-data"
        },
        # "transform": {
        #     "fact_table": "fact_regalias"
        # }
    }
    
    if not source_config:
        print("ERROR: No se encontró configuración para 'gas_natural_declaracion'")
        print("Asegúrate de que la fuente está configurada en sources_config.json")
        return False
    
    print(f"Configuración cargada:")
    print(f"   - ID: {source_config.get('id')}")
    print(f"   - Tipo: {source_config.get('type')}")
    print(f"   - Bucket: {source_config.get('storage', {}).get('bucket')}")
    print()
    
    # 2. Descargar metadata y archivos Excel del bucket
    print("Descargando archivos del bucket...")
    result = get_latest_metadata_and_excel("gas_natural_declaracion", source_config)
    
    if not result:
        print("ERROR: No se pudieron descargar archivos del bucket")
        return False
    
    metadata, excel_files = result
    
    print(f"Archivos descargados:")
    print(f"   - Metadata: extraction_date={metadata.get('extraction_date')}")
    print(f"   - Declaraciones: {metadata.get('total_declarations', 0)}")
    print(f"   - Archivos Excel: {len(excel_files)}")
    
    for filename, content in excel_files.items():
        size_kb = len(content) / 1024
        print(f"      • {filename} ({size_kb:.1f} KB)")
    print()
    
    if not excel_files:
        print("AVISO: No hay archivos Excel para transformar")
        return True
    
    # 3. Ejecutar transformación
    print("Ejecutando transformación...")
    transform_result = transform_excel_batch(
        metadata=metadata,
        excel_files=excel_files,
        source_config=source_config
    )
    
    # 4. Mostrar resultados
    stats = transform_result.get("stats", {})
    valid_records = transform_result.get("valid_records", [])
    errors = transform_result.get("errors", [])
    resoluciones = transform_result.get("resoluciones", [])
    
    print(f"\nTransformación completada:")
    print(f"   - Archivos procesados: {stats.get('total_files', 0)}")
    print(f"   - Registros válidos: {stats.get('valid', 0)}")
    print(f"   - Errores: {stats.get('errors', 0)}")
    print(f"   - Tiempo: {stats.get('processing_time_seconds', 0):.2f}s")
    print(f"   - Resoluciones extraídas: {len(resoluciones)}")
    print()
    
    # 5. Mostrar primeros registros
    if valid_records:
        print("Primeros 3 registros:")
        for i, rec in enumerate(valid_records[:3], 1):
            data = rec.get("data", {})
            print(f"\n   [{i}] {data.get('campo_nombre')}")
            print(f"       Operador: {data.get('operador')}")
            print(f"       Tipo: {data.get('tipo_produccion')}")
            print(f"       Fecha: {data.get('tiempo_fecha')}")
            print(f"       Valor: {data.get('valor_gbtud')} GBTUD")
            print(f"       Estado: {data.get('es_participacion_estado')}")
    
    # 6. Mostrar resoluciones
    if resoluciones:
        print("\nResoluciones extraídas:")
        for res in resoluciones[:5]:
            print(f"   - Res. {res.get('numero_resolucion')}: "
                  f"{res.get('periodo_desde')} - {res.get('periodo_hasta')}")
    
    # 7. Mostrar errores
    if errors:
        print(f"\nPrimeros 3 errores:")
        for i, err in enumerate(errors[:3], 1):
            print(f"   [{i}] {err.get('filename', 'N/A')}: {err.get('error', err.get('message'))}")
    
    # 8. Muestra de datos en formato tabla
    if valid_records:
        print("\n" + "-"*80)
        print("MUESTRA DE DATOS (primeros 10 registros):")
        print("-"*80)
        print(f"{'Campo':<20} {'Operador':<25} {'Tipo':<15} {'Fecha':<10} {'Valor':>10}")
        print("-"*80)
        for rec in valid_records[:10]:
            data = rec.get("data", {})
            campo = str(data.get('campo_nombre', ''))[:19]
            operador = str(data.get('operador', ''))[:24]
            tipo = str(data.get('tipo_produccion', ''))[:14]
            fecha = str(data.get('tiempo_fecha', ''))[:10]
            valor = data.get('valor_gbtud', 0)
            print(f"{campo:<20} {operador:<25} {tipo:<15} {fecha:<10} {valor:>10.3f}")
        
        # Estadísticas de valores
        valores = [r.get('data', {}).get('valor_gbtud', 0) for r in valid_records]
        ceros = sum(1 for v in valores if v == 0)
        no_ceros = len(valores) - ceros
        print(f"\nEstadísticas de valores:")
        print(f"   - Total registros: {len(valores)}")
        print(f"   - Con valor > 0: {no_ceros} ({100*no_ceros/len(valores):.1f}%)")
        print(f"   - Con valor = 0 (proyecciones): {ceros} ({100*ceros/len(valores):.1f}%)")
    
    print("\n" + "="*60)
    print("TEST COMPLETADO")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    success = test_minminas_transform()
    sys.exit(0 if success else 1)
