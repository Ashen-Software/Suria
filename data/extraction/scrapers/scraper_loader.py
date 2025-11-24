import importlib
from typing import Dict, Any
from logs_config.logger import app_logger as logger

def run_scraper_loader(source_config: Dict[str, Any], action: str = "check") -> Any:
    """
    Carga dinámicamente un módulo específico para la fuente y ejecuta la función indicada por 'action'.
    
    Convención:
    - El script debe estar en data/extraction/scrapers/
    - El nombre del archivo debe coincidir con el 'id' de la fuente (o definirse en config 'script_name').
    - Si action='check', debe tener `check(config) -> str` (hash/estado).
    - Si action='extract', debe tener `extract(config) -> Any` (descarga/proceso).
    """
    src_id = source_config.get("id")
    config = source_config.get("config", {})
    
    # Permitir override del nombre del script en el config, o usar el ID por defecto
    script_name = config.get("script_name", src_id)
    
    try:
        # Importación dinámica: extraction.scrapers.<script_name>
        module_path = f"extraction.scrapers.{script_name}"
        logger.info(f"[scraper_loader] Cargando módulo dinámico: {module_path} (Action: {action})")
        
        module = importlib.import_module(module_path)
        
        if not hasattr(module, action):
            raise AttributeError(f"El módulo {script_name} no tiene una función '{action}(config)'")
            
        # Ejecutar la función correspondiente
        func = getattr(module, action)
        result = func(source_config)
        
        return result
        
    except ImportError:
        logger.error(f"[scraper_loader] No se encontró el script para {src_id} (buscado: {script_name}.py)")
        raise
    except Exception as e:
        logger.error(f"[scraper_loader] Error ejecutando script custom {script_name}.{action}: {e}")
        raise
