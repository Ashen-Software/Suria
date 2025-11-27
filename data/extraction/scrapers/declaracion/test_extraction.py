"""
Script de test para probar la extracción de datos de declaraciones de gas natural.

Este script prueba la extracción de un solo registro y lo muestra en formato JSON.

Uso:
    python test_extraction.py              # Solo descarga, sin analizar Excel
    python test_extraction.py --excel      # Descarga y analiza Excel
"""
import json
import sys
import argparse
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from extraction.scrapers.gas_natural_declaracion import extract
from logs_config.logger import app_logger as logger


def test_single_record_extraction(analyze_excel: bool = False):
    """
    Prueba la extracción de un solo registro del Excel de declaraciones.
    
    Args:
        analyze_excel: Si es True, analiza el contenido del Excel. Si es False, solo descarga.
    """
    if analyze_excel:
        logger.info("[test_extraction] Modo: Descarga + Análisis de Excel")
    else:
        logger.info("[test_extraction] Modo: Solo extracción de enlaces (usar --excel para descargar y analizar)")
    test_config = {
        "id": "gas_natural_declaracion_test",
        "name": "Test Gas Natural Declaración",
        "config": {
            "url": "https://www.minenergia.gov.co/es/misional/hidrocarburos/funcionamiento-del-sector/gas-natural/",
            "limit_files": 1 if analyze_excel else None,
            "limit_resolutions": 1 if analyze_excel else None,
            "analyze_excel": analyze_excel
        },
        "storage": {
            "bucket": "test-raw-data"
        }
    }
    
    logger.info("[test_extraction] Iniciando test de extracción...")
    
    try:
        result_bytes = extract(test_config)
        
        if not result_bytes:
            logger.error("[test_extraction] La extracción no retornó datos")
            return
        
        result_json = json.loads(result_bytes.decode('utf-8'))
        
        declarations = result_json.get("declarations", [])
        
        if not declarations:
            logger.warning("[test_extraction] No se encontraron declaraciones extraídas")
            print("\nResultado completo:")
            print(json.dumps(result_json, indent=2, ensure_ascii=False))
            return
        
        first_declaration = declarations[0]
        declaration_title = first_declaration.get("declaration_title", "Unknown")
        resolutions = first_declaration.get("resolutions", [])
        
        print("\n" + "="*80)
        print("DECLARACIÓN EXTRAÍDA:")
        print("="*80)
        print(f"Título: {declaration_title}")
        print(f"Total resoluciones: {len(resolutions)}")
        print("="*80)
        
        if not resolutions:
            logger.warning("[test_extraction] No hay resoluciones en la declaración")
            print("\nDeclaración completa:")
            print(json.dumps(first_declaration, indent=2, ensure_ascii=False))
            return
        
        first_resolution = resolutions[0]
        
        print("\n" + "-"*80)
        print("PRIMERA RESOLUCIÓN:")
        print("-"*80)
        print(f"Número: {first_resolution.get('number')}")
        print(f"Fecha: {first_resolution.get('date')}")
        print(f"Título: {first_resolution.get('title')}")
        print(f"URL: {first_resolution.get('url')}")
        
        soporte_magnetico = first_resolution.get("soporte_magnetico")
        if soporte_magnetico:
            print(f"\nSoporte(s) Magnético(s):")
            
            if isinstance(soporte_magnetico, list):
                for idx, soporte in enumerate(soporte_magnetico, 1):
                    print(f"\n  Soporte {idx}:")
                    print(f"    Título: {soporte.get('title')}")
                    print(f"    URL: {soporte.get('url')}")
                    print(f"    Ruta local: {soporte.get('local_path', 'No guardado')}")
                    file_size_mb = soporte.get('file_size_mb')
                    if file_size_mb is not None:
                        print(f"    Tamaño: {file_size_mb:.2f} MB")
                    else:
                        print(f"    Tamaño: No descargado")
            else:
                print(f"  Título: {soporte_magnetico.get('title')}")
                print(f"  URL: {soporte_magnetico.get('url')}")
                print(f"  Ruta local: {soporte_magnetico.get('local_path', 'No guardado')}")
                file_size_mb = soporte_magnetico.get('file_size_mb')
                if file_size_mb is not None:
                    print(f"  Tamaño: {file_size_mb:.2f} MB")
                else:
                    print(f"  Tamaño: No descargado")
        
        extracted_data = first_resolution.get("extracted_data")
        
        if extracted_data:
            first_record = extracted_data[0]
            
            print("\n" + "-"*80)
            print("PRIMER REGISTRO EXTRAÍDO DEL EXCEL:")
            print("-"*80)
            print(f"Hoja: {first_record.get('sheet_name')}")
            print(f"Campo: {first_record.get('field')}")
            print(f"Contrato: {first_record.get('contract')}")
            print(f"Operador: {first_record.get('operator')}")
            print(f"Poder Calorífico: {first_record.get('calorific_power_btu_pc')}")
            print(f"Entidad: {first_record.get('entity')}")
            print(f"Categoría: {first_record.get('category')}")
            print(f"Periodo: {first_record.get('period')}")
            print(f"Datos mensuales: {len(first_record.get('monthly_data', {}))} meses")
            
            monthly_data = first_record.get('monthly_data', {})
            if monthly_data:
                print("\nDatos mensuales (primeros no-cero):")
                count = 0
                for month, value in monthly_data.items():
                    if value != 0.0 and count < 5:
                        print(f"  {month.upper()}: {value}")
                        count += 1
        else:
            print("\n" + "-"*80)
            print("ANÁLISIS DE EXCEL:")
            print("-"*80)
            if analyze_excel:
                print("Análisis activado pero no se encontraron datos extraídos del Excel")
            else:
                print("Análisis de Excel desactivado (usar --excel para activarlo)")
        
        print("\n" + "-"*80)
        print("ARCHIVOS GUARDADOS:")
        print("-"*80)
        from extraction.scrapers.declaracion.file_manager import RAW_DIR, PROCESSED_DIR
        print(f"Excel guardados en: {RAW_DIR}")
        print(f"JSON guardado en: {PROCESSED_DIR}")
        
        print("\n" + "="*80)
        print("RESUMEN COMPLETO (JSON):")
        print("="*80)
        print(json.dumps(first_declaration, indent=2, ensure_ascii=False))
        print("="*80)
        
        logger.info("[test_extraction] Test completado exitosamente")
        
    except Exception as e:
        logger.error(f"[test_extraction] Error en test: {e}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test de extracción de declaraciones de gas natural')
    parser.add_argument(
        '--excel',
        action='store_true',
        help='Activa el análisis del contenido del Excel (por defecto está desactivado)'
    )
    
    args = parser.parse_args()
    
    test_single_record_extraction(analyze_excel=args.excel)

