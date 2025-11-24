import os
import requests
from datetime import datetime
from services.backend_client import BackendClient
from logs_config.logger import app_logger as logger

def _resolve_env_vars(value: str) -> str:
    """
    Si un valor comienza con $, lo interpreta como variable de entorno.
    Ejemplo: "$API_TOKEN" -> valor de os.getenv("API_TOKEN")
    """
    if isinstance(value, str) and value.startswith("$"):
        env_var = value[1:]  # Quita el $
        env_value = os.getenv(env_var)
        if env_value is None:
            logger.warning(f"[api_loader] Variable de entorno '{env_var}' no encontrada, usando valor como está")
            return value
        return env_value
    return value

def _resolve_dict_env_vars(obj):
    """
    Resuelve variables de entorno en todos los valores de un diccionario (recursivamente).
    """
    if isinstance(obj, dict):
        return {k: _resolve_dict_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_dict_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        return _resolve_env_vars(obj)
    else:
        return obj

def run_api_loader(source_config: dict):
    """
    Hace GET a base_url con headers y params del config y guarda en Supabase Storage.
    Soporta autenticación mediante variables de entorno.
    Variables de entorno: cualquier valor que comience con $ será resuelto (ej: "$API_TOKEN").
    """
    url = source_config.get("config", {}).get("base_url")
    params = source_config.get("config", {}).get("params", {})
    headers = source_config.get("config", {}).get("headers", {}).copy()  # Copia para no mutar original
    
    # Resolver variables de entorno en params y headers
    params = _resolve_dict_env_vars(params)
    headers = _resolve_dict_env_vars(headers)
    
    # Configuracion de autenticacion
    auth_type = source_config.get("config", {}).get("auth_type")
    auth_key_env = source_config.get("config", {}).get("auth_key_env")
    
    if auth_key_env and auth_type:
        api_key = os.getenv(auth_key_env)
        if not api_key:
            logger.error(f"[api_loader] Variable de entorno '{auth_key_env}' no está definida")
            raise ValueError(f"Variable de entorno '{auth_key_env}' requerida pero no encontrada")
        
        if auth_type == "bearer":
            headers["Authorization"] = f"Bearer {api_key}"
        elif auth_type == "api_key":
            headers["X-API-Key"] = api_key
        elif auth_type == "custom_header":
            # Permite especificar el nombre del header en config
            custom_header = source_config.get("config", {}).get("auth_header_name", "Authorization")
            headers[custom_header] = api_key
        else:
            logger.warning(f"[api_loader] Tipo de autenticación '{auth_type}' no reconocido")
    
    # Configuracion de Storage
    storage_config = source_config.get("storage", {})
    bucket_name = storage_config.get("bucket", "raw-data")
    
    # Generar path historico por defecto: api/{id}/YYYY-MM-DD_HHMMSS.json
    now = datetime.now()
    timestamp_path = now.strftime("%Y-%m-%d_%H%M%S")
    default_path = f"api/{source_config.get('id')}/{timestamp_path}.json"
    
    remote_path = storage_config.get("path", default_path)

    try:
        # Configuración de reintentos (opcional)
        max_retries = source_config.get("config", {}).get("max_retries", 3)
        timeout = source_config.get("config", {}).get("timeout", 60)
        
        r = requests.get(url, params=params, headers=headers, timeout=timeout)
        r.raise_for_status()
        
        # Subir a Supabase Storage
        client = BackendClient()
        client.upload_file(
            bucket_name=bucket_name,
            file_path=remote_path,
            file_content=r.content,
            content_type="application/json"
        )
        logger.info(f"[api_loader] Datos descargados y guardados desde {url}")
        
    except Exception as e:
        logger.exception(f"[api_loader] Error descargando {url}: {e}")
        raise
