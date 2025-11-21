from loguru import logger

def run_scraper_loader(source_config: dict):
    """
    Placeholder: aquí se integraría Playwright.
    """
    logger.info(f"[scraper_loader] Ejecutando scraper para {source_config.get('id')}")
    # logic: lanzar playwright, navegar, descargar archivos o extraer fecha
    # guardar en storage.local_raw_path
