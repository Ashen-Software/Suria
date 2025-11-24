import importlib
from typing import Dict, Any
from logs_config.logger import app_logger as logger

def run_scraper_loader(source_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Carga dinámicamente un módulo específico para la fuente y ejecuta su función 'check'.
    
    Convención:
    - El script debe estar en data/extraction/scrapers/
    - El nombre del archivo debe coincidir con el 'id' de la fuente (o definirse en config 'script_name').
    - El script debe tener una función `check(config) -> str` que retorne el hash/estado actual.
    """
    src_id = source_config.get("id")
    config = source_config.get("config", {})
    
    # Permitir override del nombre del script en el config, o usar el ID por defecto
    script_name = config.get("script_name", src_id)
    
    try:
        # Importación dinámica: extraction.scrapers.<script_name>
        module_path = f"extraction.scrapers.{script_name}"
        logger.info(f"[scraper_loader] Cargando módulo dinámico: {module_path}")
        
        module = importlib.import_module(module_path)
        
        if not hasattr(module, "check"):
            raise AttributeError(f"El módulo {script_name} no tiene una función 'check(config)'")
            
        # Ejecutar la lógica personalizada
        # Se espera que retorne el valor para hashear o el hash directo
        result = module.check(source_config)
        
        return result
        
    except ImportError:
        logger.error(f"[scraper_loader] No se encontró el script para {src_id} (buscado: {script_name}.py)")
        raise
    except Exception as e:
        logger.error(f"[scraper_loader] Error ejecutando script custom {script_name}: {e}")
        raise
