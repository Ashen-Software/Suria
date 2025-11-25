"""
Gestión de archivos RAW en Storage.

Responsable de:
- Listar archivos por lote (timestamp)
- Descargar archivos en memoria
- Validación básica de JSON
"""
from typing import List, Optional, Dict, Tuple
from services.backend_client import BackendClient
from logs_config.logger import app_logger as logger
import json


def get_latest_raw_files(source_id: str, source_config: Dict) -> Optional[List[Tuple[str, str]]]:
    """
    Obtiene TODOS los archivos RAW del lote más reciente de Storage.
    
    Maneja dos escenarios:
    1. Archivo único: api/{id}/YYYY-MM-DD_HHMMSS.json
    2. Múltiples páginas: api/{id}/YYYY-MM-DD_HHMMSS/page_*.json
    
    Args:
        source_id: ID de la fuente (ej: "api_regalias")
        source_config: Config de la fuente (contiene bucket)
        
    Returns:
        List de tuplas (file_path, content_str) con los archivos más recientes, o None si error
    """
    try:
        client = BackendClient()
        bucket_name = source_config.get("storage", {}).get("bucket", "raw-data")
        prefix = f"api/{source_id}/"
        
        # Listar archivos en el prefijo
        files = client.list_files(bucket_name, prefix)
        
        if not files:
            logger.warning(f"[storage] No hay archivos en {bucket_name}/{prefix}")
            return None
        
        # Detectar si es archivo unico o lote con paginas
        # Archivos unicos: api/id/2024-11-25_120000.json
        # Lotes: api/id/2024-11-25_120000/page_0001.json, page_0002.json, ...
        
        # Agrupar por timestamp (ej: "2024-11-25_120000")
        files_by_timestamp = {}
        for f in files:
            # Extraer timestamp del path
            # api/api_regalias/2024-11-25_120000.json → 2024-11-25_120000
            # api/api_regalias/2024-11-25_120000/page_0001.json → 2024-11-25_120000
            parts = f.split('/')
            if len(parts) >= 3:
                timestamp = parts[-2] if 'page_' in parts[-1] else parts[-1].split('.')[0]
                if timestamp not in files_by_timestamp:
                    files_by_timestamp[timestamp] = []
                files_by_timestamp[timestamp].append(f)
        
        if not files_by_timestamp:
            logger.warning(f"[storage] No se pudieron agrupar archivos por timestamp")
            return None
        
        # Obtener archivos del timestamp mas reciente
        latest_timestamp = sorted(files_by_timestamp.keys())[-1]
        latest_files = sorted(files_by_timestamp[latest_timestamp])
        
        logger.info(f"[storage] Lote detectado: {latest_timestamp} con {len(latest_files)} archivo(s)")
        
        # Descargar todos los archivos del lote EN MEMORIA
        result = []
        for file_path in latest_files:
            try:
                # Descargar del bucket (retorna bytes)
                content_bytes = client.download_file(bucket_name, file_path)
                
                if content_bytes is None:
                    logger.warning(f"[storage] Archivo vacío o no descargado: {file_path}")
                    continue
                
                # Convertir bytes a string
                if isinstance(content_bytes, bytes):
                    content_str = content_bytes.decode('utf-8')
                else:
                    content_str = str(content_bytes)
                
                # Validar que es JSON valido
                try:
                    json.loads(content_str)
                except json.JSONDecodeError as je:
                    logger.error(f"[storage] Contenido JSON inválido en {file_path}: {je}")
                    continue
                
                result.append((file_path, content_str))
                logger.info(f"[storage] Archivo descargado en memoria: {file_path} ({len(content_str)} bytes)")
                
            except Exception as e:
                logger.error(f"[storage] Error descargando {file_path}: {e}")
                import traceback
                traceback.print_exc()
                # Continuar con otros archivos
        
        if not result:
            logger.error(f"[storage] No se descargó ningún archivo válido para {source_id}")
            return None
        
        return result
        
    except Exception as e:
        logger.error(f"[storage] Error obteniendo archivos RAW: {e}")
        import traceback
        traceback.print_exc()
        return None
