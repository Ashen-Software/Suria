from loguru import logger
from typing import List, Dict

def full_etl_task(changed_sources: List[str], current_config: Dict):
    """
    Recibe la lista de fuentes cambiadas y ejecuta la extracción por cada una.
    """
    if not current_config:
        logger.error("[full_etl] No hay config disponible.")
        return

    sources_map = {s["id"]: s for s in current_config.get("sources", [])}
    for src_id in changed_sources:
        src = sources_map.get(src_id)
        if not src:
            logger.warning(f"[full_etl] Fuente no encontrada en config: {src_id}")
            continue

        logger.info(f"[full_etl] Ejecutando extracción para {src_id} (type={src.get('type')})")
        # Llamar al loader correspondiente: api_loader, scraper_loader, etc.
        typ = src.get("type")
        if typ == "api":
            # from extraction.api_clients.api_loader import run as run_api
            # run_api(src)
            logger.info(f"[full_etl] (sim) api_loader para {src_id}")
        elif typ in ("scrape", "scraper"):
            # from extraction.scrapers.scraper_loader import run as run_scraper
            # run_scraper(src)
            logger.info(f"[full_etl] (sim) scraper_loader para {src_id}")
        else:
            logger.warning(f"[full_etl] Tipo no soportado: {typ}")
