import os
import json
import requests
from datetime import datetime
from services.backend_client import BackendClient
from common.env_resolver import resolve_dict_env_vars
from logs_config.logger import app_logger as logger

def run_api_loader(source_config: dict):
    """
    Hace GET a base_url con headers y params del config y guarda en Supabase Storage.
    Soporta variables de entorno ($VARIABLE) y paginación (Socrata).
    
    Para paginación (Socrata), usar:
    {
      "pagination": {
        "enabled": true,
        "limit": 50000,
        "offset_param": "$offset",
        "limit_param": "$limit"
      }
    }
    """
    url = source_config.get("config", {}).get("base_url")
    params = source_config.get("config", {}).get("params", {})
    headers = source_config.get("config", {}).get("headers", {}).copy()
    
    # Resolver variables de entorno en params y headers
    params = resolve_dict_env_vars(params)
    headers = resolve_dict_env_vars(headers)
    
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
            custom_header = source_config.get("config", {}).get("auth_header_name", "Authorization")
            headers[custom_header] = api_key
        else:
            logger.warning(f"[api_loader] Tipo de autenticación '{auth_type}' no reconocido")
    
    # Configuracion de Storage
    storage_config = source_config.get("storage", {})
    bucket_name = storage_config.get("bucket", "raw-data")
    
    # Configuracion de paginacion
    pagination_config = source_config.get("config", {}).get("pagination", {})
    pagination_enabled = pagination_config.get("enabled", False)
    
    try:
        timeout = source_config.get("config", {}).get("timeout", 60)
        
        if pagination_enabled:
            _load_paginated_data(
                url=url,
                params=params,
                headers=headers,
                bucket_name=bucket_name,
                source_id=source_config.get("id"),
                pagination_config=pagination_config,
                timeout=timeout
            )
        else:
            _load_single_request(
                url=url,
                params=params,
                headers=headers,
                bucket_name=bucket_name,
                source_id=source_config.get("id"),
                timeout=timeout
            )
        
        logger.info(f"[api_loader] Datos descargados y guardados desde {url}")
        
    except Exception as e:
        logger.exception(f"[api_loader] Error descargando {url}: {e}")
        raise


def _load_single_request(url: str, params: dict, headers: dict, bucket_name: str, 
                         source_id: str, timeout: int):
    """Carga datos con una sola petición (para APIs sin paginación)."""
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Generar path: api/{id}/YYYY-MM-DD_HHMMSS.json
        now = datetime.now()
        timestamp_path = now.strftime("%Y-%m-%d_%H%M%S")
        remote_path = f"api/{source_id}/{timestamp_path}.json"
        
        # Subir a Supabase Storage
        client = BackendClient()
        client.upload_file(
            bucket_name=bucket_name,
            file_path=remote_path,
            file_content=response.content,
            content_type="application/json"
        )
        logger.info(f"[api_loader] Archivo guardado: {remote_path}")
        
    except requests.exceptions.Timeout:
        logger.error(f"[api_loader] Timeout al acceder a {url}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"[api_loader] Error en request: {e}")
        raise


def _load_paginated_data(url: str, params: dict, headers: dict, bucket_name: str,
                         source_id: str, pagination_config: dict, timeout: int):
    """
    Carga datos con paginación (ej: Socrata).
    
    Soporta dos estilos de paginación:
    1. Offset-based: offset_param, limit_param (ej: $offset, $limit)
    2. Page-based: page_param, size_param (ej: pageNumber, pageSize)
    """
    # Detectar tipo de paginacion
    page_param = pagination_config.get("page_param")
    size_param = pagination_config.get("size_param")
    offset_param = pagination_config.get("offset_param")
    limit_param = pagination_config.get("limit_param")
    
    page_size = pagination_config.get("page_size", 50000)
    
    # Generar base path con timestamp
    now = datetime.now()
    timestamp_path = now.strftime("%Y-%m-%d_%H%M%S")
    base_path = f"api/{source_id}/{timestamp_path}"
    
    page_num = 1
    total_rows = 0
    
    client = BackendClient()
    
    try:
        while True:
            # Preparar parametros para esta pagina
            page_params = params.copy()
            
            if page_param and size_param:
                # Estilo page-based (Socrata: pageNumber=1, pageSize=10000)
                page_params[page_param] = page_num
                page_params[size_param] = page_size
                logger.info(f"[api_loader] Descargando página {page_num} ({page_param}={page_num}, {size_param}={page_size})")
            elif offset_param and limit_param:
                # Estilo offset-based
                offset = (page_num - 1) * page_size
                page_params[offset_param] = offset
                page_params[limit_param] = page_size
                logger.info(f"[api_loader] Descargando página {page_num} (offset={offset}, limit={page_size})")
            else:
                logger.error("[api_loader] Configuración de paginación incompleta: requiere (page_param, size_param) o (offset_param, limit_param)")
                raise ValueError("Configuración de paginación inválida")
            
            response = requests.get(url, params=page_params, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error(f"[api_loader] Respuesta no es JSON válido")
                raise
            
            # Guardar pagina individual
            page_path = f"{base_path}/page_{page_num:04d}.json"
            client.upload_file(
                bucket_name=bucket_name,
                file_path=page_path,
                file_content=json.dumps(data).encode('utf-8'),
                content_type="application/json"
            )
            logger.info(f"[api_loader] Página {page_num} guardada: {page_path}")
            
            # Extraer filas (Socrata: {"data": [...], ...})
            rows = data.get("data", []) if isinstance(data, dict) else data
            if not rows:
                logger.info(f"[api_loader] Paginación completada: {page_num - 1} páginas, {total_rows} filas totales")
                break
            
            total_rows += len(rows)
            
            # Si la pagina tiene menos filas que el limite, es la ultima
            if len(rows) < page_size:
                logger.info(f"[api_loader] Última página detectada (solo {len(rows)} filas < {page_size})")
                break
            
            page_num += 1
        
    except requests.exceptions.Timeout:
        logger.error(f"[api_loader] Timeout en paginación en página {page_num}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"[api_loader] Error en request de paginación: {e}")
        raise
