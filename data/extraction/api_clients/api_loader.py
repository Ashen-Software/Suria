from loguru import logger
import requests
import os

def run_api_loader(source_config: dict):
    """
    Ejemplo básico: hace GET a base_url con headers y params del config y guarda en local_raw_path.
    """
    url = source_config.get("config", {}).get("base_url")
    params = source_config.get("config", {}).get("params", {})
    headers = source_config.get("config", {}).get("headers", {})
    raw_path = source_config.get("storage", {}).get("local_raw_path", "/app/data/raw/")

    try:
        r = requests.get(url, params=params, headers=headers, timeout=60)
        r.raise_for_status()
        os.makedirs(raw_path, exist_ok=True)
        file_name = os.path.join(raw_path, "data_" + source_config.get("id") + ".json")
        with open(file_name, "wb") as f:
            f.write(r.content)
        logger.info(f"[api_loader] Guardado raw -> {file_name}")
    except Exception as e:
        logger.exception(f"[api_loader] Error descargando {url}: {e}")
