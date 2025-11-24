import requests
import os
from datetime import datetime
from services.backend_client import BackendClient
from logs_config.logger import app_logger as logger

def run_api_loader(source_config: dict):
    """
    Hace GET a base_url con headers y params del config y guarda en Supabase Storage.
    """
    url = source_config.get("config", {}).get("base_url")
    params = source_config.get("config", {}).get("params", {})
    headers = source_config.get("config", {}).get("headers", {})
    
    # Configuracion de Storage
    storage_config = source_config.get("storage", {})
    bucket_name = storage_config.get("bucket", "raw-data")
    
    # Generar path historico por defecto: api/{id}/YYYY-MM-DD_HHMMSS.json
    now = datetime.now()
    timestamp_path = now.strftime("%Y-%m-%d_%H%M%S")
    default_path = f"api/{source_config.get('id')}/{timestamp_path}.json"
    
    remote_path = storage_config.get("path", default_path)

    try:
        r = requests.get(url, params=params, headers=headers, timeout=60)
        r.raise_for_status()
        
        # Subir a Supabase Storage
        client = BackendClient()
        client.upload_file(
            bucket_name=bucket_name,
            file_path=remote_path,
            file_content=r.content,
            content_type="application/json"
        )
        
    except Exception as e:
        logger.exception(f"[api_loader] Error descargando {url}: {e}")
