"""
Script de prueba para verificar el flujo de Extraction.

Uso:
    cd data
    python -m workflows.tests.test_extraction --source gas_natural_declaracion

Este script prueba la extracción de una fuente sin ejecutar el ETL completo.
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from logs_config.logger import app_logger as logger
from workflows.full_etl.extractors import get_extractor
from services.config_manager import ConfigManager


def test_extraction(source_id: str, dry_run: bool = False):
    """
    Prueba la extracción para una fuente específica.
    
    Args:
        source_id: ID de la fuente a probar
        dry_run: Si True, ejecuta el scraper pero no sube al bucket
    """
    logger.info("=" * 60)
    logger.info(f"TEST: Extraction - {source_id}")
    logger.info("=" * 60)
    
    config_manager = ConfigManager()
    current_config = config_manager.get_config()
    
    if not current_config:
        logger.error("No se pudo cargar la configuración")
        return False
    
    sources = current_config.get("sources", [])
    source_config = None
    
    for src in sources:
        if src.get("id") == source_id:
            source_config = src
            break
    
    if not source_config:
        logger.error(f"Fuente '{source_id}' no encontrada en sources_config.json")
        logger.info("Fuentes disponibles:")
        for src in sources:
            logger.info(f"  - {src.get('id')}: {src.get('name')}")
        return False
    
    logger.info(f"Fuente: {source_config.get('name')}")
    logger.info(f"Tipo: {source_config.get('type')}")
    logger.info(f"Bucket: {source_config.get('storage', {}).get('bucket')}")
    logger.info("-" * 60)
    
    src_type = source_config.get("type")
    extractor = get_extractor(src_type)
    
    if not extractor:
        logger.error(f"No hay extractor para tipo '{src_type}'")
        return False
    
    logger.info(f"Extractor: {extractor.__class__.__name__}")
    
    if dry_run:
        logger.info("\n[DRY RUN] Ejecutando scraper sin subir al bucket...")
        return test_extraction_dry_run(source_config)
    
    # Ejecutar extracción completa
    try:
        logger.info("\nIniciando extracción...")
        extractor.extract(source_config)
        
        logger.info("-" * 60)
        logger.info("Extracción completada")
        return True
        
    except Exception as e:
        logger.error(f"ERROR durante extracción: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_extraction_dry_run(source_config: dict):
    """
    Ejecuta el scraper pero no sube archivos al bucket.
    Útil para verificar que el scraper funciona correctamente.
    """
    from extraction.scrapers.scraper_loader import run_scraper_loader
    
    try:
        result = run_scraper_loader(source_config, action="extract")
        
        if not result:
            logger.warning("El scraper no retornó datos")
            return False
        
        # Analizar resultado
        if isinstance(result, dict) and "metadata" in result:
            # Formato estructurado
            metadata = result.get("metadata")
            if isinstance(metadata, bytes):
                metadata = metadata.decode('utf-8')
            
            meta_dict = json.loads(metadata)
            excel_files = result.get("excel_files", [])
            
            logger.info("\nRESULTADO (formato estructurado):")
            logger.info(f"   Fecha extracción: {meta_dict.get('extraction_date')}")
            logger.info(f"   Total declaraciones: {meta_dict.get('total_declarations')}")
            logger.info(f"   Archivos Excel: {len(excel_files)}")
            
            if excel_files:
                logger.info("\nArchivos Excel descargados:")
                for ef in excel_files:
                    size_mb = len(ef.get('content', b'')) / (1024 * 1024)
                    parsed = "✓" if ef.get('parsed_data') else "✗"
                    logger.info(f"      - {ef.get('filename')}: {size_mb:.2f} MB (parsed: {parsed})")
            
            # Mostrar estructura de declaraciones
            declarations = meta_dict.get("declarations", [])
            if declarations:
                logger.info(f"\nDeclaraciones ({len(declarations)}):")
                for decl in declarations[:3]:  # Mostrar máximo 3
                    title = decl.get("declaration_title", "Unknown")
                    resolutions = len(decl.get("resolutions", []))
                    logger.info(f"      - {title}: {resolutions} resoluciones")
                if len(declarations) > 3:
                    logger.info(f"      ... y {len(declarations) - 3} más")
        
        else:
            # Formato simple
            content = result if isinstance(result, bytes) else result.encode('utf-8')
            logger.info(f"\nRESULTADO (formato simple):")
            logger.info(f"   Tamaño: {len(content)} bytes")
        
        logger.info("\n" + "-" * 60)
        logger.info("Dry run completado - datos listos para subir al bucket")
        return True
        
    except Exception as e:
        logger.error(f"ERROR en dry run: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Extraction para fuentes ETL")
    parser.add_argument(
        "--source", "-s",
        required=True,
        help="ID de la fuente a probar (ej: gas_natural_declaracion)"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Ejecutar scraper sin subir al bucket"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("  TEST EXTRACTION")
    print("=" * 60 + "\n")
    
    success = test_extraction(args.source, args.dry_run)
    
    print("\n" + "=" * 60)
    if success:
        print("TEST COMPLETADO")
    else:
        print("TEST FALLIDO")
    print("=" * 60 + "\n")
    
    sys.exit(0 if success else 1)
