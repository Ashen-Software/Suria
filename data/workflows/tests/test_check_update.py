"""
Script de prueba para verificar el flujo de Check Updates.

Uso:
    cd data
    python -m workflows.tests.test_check_update

Este script prueba el check update de la fuente gas_natural_declaracion
sin ejecutar el ETL completo.
"""
import sys
import os

# Asegurar que el directorio data está en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from logs_config.logger import app_logger as logger
from workflows.check_updates.run import check_updates_task
from services.config_manager import ConfigManager


def test_check_update_gas_natural():
    """
    Prueba el check update para gas_natural_declaracion.
    """
    logger.info("=" * 60)
    logger.info("TEST: Check Update - gas_natural_declaracion")
    logger.info("=" * 60)
    
    config_manager = ConfigManager()
    current_config = config_manager.get_config()
    
    if not current_config:
        logger.error("No se pudo cargar la configuración")
        return False
    
    sources = current_config.get("sources", [])
    gas_source = None
    
    for src in sources:
        if src.get("id") == "gas_natural_declaracion":
            gas_source = src
            break
    
    if not gas_source:
        logger.error("Fuente 'gas_natural_declaracion' no encontrada en sources_config.json")
        return False
    
    logger.info(f"Fuente encontrada: {gas_source.get('name')}")
    logger.info(f"Tipo: {gas_source.get('type')}")
    logger.info(f"URL: {gas_source.get('config', {}).get('url')}")
    logger.info("-" * 60)
    
    # Ejecutar check update
    try:
        has_changes = check_updates_task(gas_source)
        
        logger.info("-" * 60)
        if has_changes:
            logger.info("RESULTADO: Se detectaron CAMBIOS en la fuente")
        else:
            logger.info("RESULTADO: Sin cambios detectados")
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR durante check update: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_check_update_manual():
    """
    Prueba el check update con configuración manual (sin BD).
    Útil para probar sin conexión a Supabase.
    """
    logger.info("=" * 60)
    logger.info("TEST: Check Update Manual (sin BD)")
    logger.info("=" * 60)
    
    # Configuración manual de la fuente
    source_config = {
        "id": "gas_natural_declaracion",
        "name": "Declaraciones de Producción de Gas Natural - MinEnergía",
        "type": "complex_scraper",
        "active": True,
        "config": {
            "script_name": "gas_natural_declaracion",
            "url": "https://www.minenergia.gov.co/es/misional/hidrocarburos/funcionamiento-del-sector/gas-natural/",
            "analyze_excel": False
        },
        "storage": {
            "bucket": "raw-data",
            "path_prefix": "complex/gas_natural_declaracion"
        }
    }
    
    logger.info(f"Probando fuente: {source_config['id']}")
    logger.info("-" * 60)
    
    # Importar directamente el scraper para probar
    from extraction.scrapers.scraper_loader import run_scraper_loader
    
    try:
        # Ejecutar solo la función check del scraper
        checksum = run_scraper_loader(source_config, action="check")
        
        logger.info("-" * 60)
        logger.info(f"✅ Check ejecutado exitosamente")
        logger.info(f"   Checksum generado: {checksum}")
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Check Update para gas_natural_declaracion")
    parser.add_argument(
        "--manual", 
        action="store_true", 
        help="Ejecutar en modo manual (sin BD)"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Forzar cambio (simular que hubo cambios)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("  TEST CHECK UPDATE - Gas Natural Declaración")
    print("=" * 60 + "\n")
    
    if args.manual:
        success = test_check_update_manual()
    else:
        success = test_check_update_gas_natural()
    
    print("\n" + "=" * 60)
    if success:
        print("TEST COMPLETADO")
    else:
        print("TEST FALLIDO")
    print("=" * 60 + "\n")
    
    sys.exit(0 if success else 1)
