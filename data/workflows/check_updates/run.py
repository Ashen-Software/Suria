from loguru import logger
from typing import List, Dict

def check_updates_task(current_config: Dict) -> List[str]:
    """
    Recorre las fuentes definidas en current_config y devuelve lista de source_ids que cambiaron.
    Por ahora el skeleton simplemente simula la detección.
    """
    changed = []
    if not current_config:
        logger.warning("[check_updates] No hay config cargado.")
        return changed

    for src in current_config.get("sources", []):
        # placeholder: implementar chequear (api_timestamp, scrape_text, list_files, checksum)
        src_id = src.get("id")
        logger.info(f"[check_updates] Verificando fuente: {src_id}")
        # SIMULACIÓN: marcar cambio si el flag `force_change` está presente (solo para testing)
        if src.get("force_change", False):
            changed.append(src_id)
    return changed
