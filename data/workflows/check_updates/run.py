from logs_config.logger import app_logger as logger
from typing import List, Dict
from services.backend_client import BackendClient
from .checkers import get_checker

def check_updates_task(source_config: Dict) -> bool:
    """
    Verifica una fuente definida en source_config.
    Retorna True si se detectaron cambios, False en caso contrario.
    """
    if not source_config:
        logger.warning("[check_updates] Configuración de fuente vacía.")
        return False

    # Instanciar cliente de backend
    backend_client = BackendClient()

    src = source_config
    src_id = src.get("id")
    src_type = src.get("type")
    
    logger.info(f"[check_updates] Verificando fuente: {src_id} (Tipo: {src_type})")
    
    # Verificar flag manual de cambio forzado (dev/testing)
    if src.get("force_change", False):
        logger.info(f"[check_updates] Cambio forzado detectado en {src_id}")
        return True

    # Obtener checker especifico
    checker = get_checker(src_type, backend_client)
    if not checker:
        logger.warning(f"[check_updates] No hay checker implementado para tipo '{src_type}' en {src_id}")
        return False

    try:
        has_changes = checker.check(src)
        if has_changes:
            # El checker actualiza el estado en el backend si detecto cambio
            return True
    except Exception as e:
        logger.error(f"[check_updates] Error crítico verificando {src_id}: {e}")

    return False
