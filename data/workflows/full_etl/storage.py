"""
Gestión de archivos RAW en Storage.

Responsable de:
- Listar archivos por lote (timestamp)
- Descargar archivos en memoria (JSON y Excel)
- Validación básica de JSON

Estructuras soportadas:
1. API simple: api/{id}/YYYY-MM-DD_HHMMSS.json
2. API paginada: api/{id}/YYYY-MM-DD_HHMMSS/page_*.json
3. Complex scraper simple: complex/{id}/YYYY-MM-DD_HHMMSS.json
4. Complex scraper estructurado: complex/{id}/YYYY-MM-DD_HHMMSS/
       metadata.json
       excel/*.xlsx
       parsed/*.json
"""
from typing import List, Optional, Dict, Tuple, Any
from services.backend_client import BackendClient
from logs_config.logger import app_logger as logger
import json


def get_latest_raw_files(source_id: str, source_config: Dict) -> Optional[List[Tuple[str, str]]]:
    """
    Obtiene archivos RAW del lote más reciente de Storage.
    
    Para complex_scraper con estructura (metadata + excel + parsed):
    - Retorna metadata.json y todos los parsed/*.json
    - Los Excel originales no se retornan (son respaldo)
    
    Args:
        source_id: ID de la fuente
        source_config: Config de la fuente (contiene bucket, type)
        
    Returns:
        List de tuplas (file_path, content_str) con los archivos JSON, o None si error
    """
    try:
        client = BackendClient()
        bucket_name = source_config.get("storage", {}).get("bucket", "raw-data")
        source_type = source_config.get("type", "api")
        
        # Determinar prefijo según tipo de fuente
        if source_type == "complex_scraper":
            path_prefix = source_config.get("storage", {}).get("path_prefix", f"complex/{source_id}")
            prefix = f"{path_prefix}/"
        else:
            prefix = f"api/{source_id}/"
        
        # Listar archivos en el prefijo
        files = client.list_files(bucket_name, prefix)
        
        if not files:
            logger.warning(f"[storage] No hay archivos en {bucket_name}/{prefix}")
            return None
        
        # Agrupar por timestamp
        files_by_timestamp = _group_files_by_timestamp(files, prefix)
        
        if not files_by_timestamp:
            logger.warning(f"[storage] No se pudieron agrupar archivos por timestamp")
            return None
        
        # Obtener archivos del timestamp más reciente
        latest_timestamp = sorted(files_by_timestamp.keys())[-1]
        latest_files = files_by_timestamp[latest_timestamp]
        
        logger.info(f"[storage] Lote detectado: {latest_timestamp} con {len(latest_files)} archivo(s)")
        
        # Filtrar: solo archivos JSON (excluir Excel binarios)
        json_files = [f for f in latest_files if f.endswith('.json')]
        
        # Ordenar: metadata.json primero, luego parsed/*.json
        json_files = sorted(json_files, key=lambda x: (
            0 if 'metadata.json' in x else 1,
            x
        ))
        
        logger.info(f"[storage] Archivos JSON a procesar: {len(json_files)}")
        
        # Descargar archivos JSON en memoria
        result = _download_json_files(client, bucket_name, json_files)
        
        if not result:
            logger.error(f"[storage] No se descargó ningún archivo válido para {source_id}")
            return None
        
        return result
        
    except Exception as e:
        logger.error(f"[storage] Error obteniendo archivos RAW: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_latest_excel_files(source_id: str, source_config: Dict) -> Optional[Dict[str, bytes]]:
    """
    Obtiene archivos Excel RAW del lote más reciente de Storage.
    
    Para complex_scraper con estructura (metadata + excel/*.xlsx):
    - Retorna diccionario {filename: bytes} con archivos Excel
    
    Args:
        source_id: ID de la fuente
        source_config: Config de la fuente (contiene bucket, type)
        
    Returns:
        Dict de {filename: bytes} con archivos Excel, o None si error
    """
    try:
        client = BackendClient()
        bucket_name = source_config.get("storage", {}).get("bucket", "raw-data")
        source_type = source_config.get("type", "api")
        
        if source_type != "complex_scraper":
            logger.warning(f"[storage] get_latest_excel_files solo soporta complex_scraper")
            return None
        
        path_prefix = source_config.get("storage", {}).get("path_prefix", f"complex/{source_id}")
        prefix = f"{path_prefix}/"
        
        # Listar archivos en el prefijo
        files = client.list_files(bucket_name, prefix)
        
        if not files:
            logger.warning(f"[storage] No hay archivos en {bucket_name}/{prefix}")
            return None
        
        # Agrupar por timestamp
        files_by_timestamp = _group_files_by_timestamp(files, prefix)
        
        if not files_by_timestamp:
            logger.warning(f"[storage] No se pudieron agrupar archivos por timestamp")
            return None
        
        # Obtener archivos del timestamp más reciente
        latest_timestamp = sorted(files_by_timestamp.keys())[-1]
        latest_files = files_by_timestamp[latest_timestamp]
        
        logger.info(f"[storage] Lote detectado: {latest_timestamp} con {len(latest_files)} archivo(s)")
        
        # Filtrar: solo archivos Excel en la carpeta excel/
        excel_files = [
            f for f in latest_files 
            if '/excel/' in f and (f.endswith('.xlsx') or f.endswith('.xlsm') or f.endswith('.xls'))
        ]
        
        logger.info(f"[storage] Archivos Excel encontrados: {len(excel_files)}")
        
        if not excel_files:
            logger.warning(f"[storage] No hay archivos Excel en el lote {latest_timestamp}")
            return None
        
        # Descargar archivos Excel en memoria
        result = _download_excel_files(client, bucket_name, excel_files)
        
        if not result:
            logger.error(f"[storage] No se descargó ningún archivo Excel para {source_id}")
            return None
        
        return result
        
    except Exception as e:
        logger.error(f"[storage] Error obteniendo archivos Excel: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_latest_metadata_and_excel(
    source_id: str, 
    source_config: Dict
) -> Optional[Tuple[Dict[str, Any], Dict[str, bytes]]]:
    """
    Obtiene metadata.json y archivos Excel del lote más reciente.
    
    Combina get_latest_raw_files y get_latest_excel_files para
    obtener tanto la metadata (con info de resoluciones) como los
    archivos Excel binarios.
    
    Args:
        source_id: ID de la fuente
        source_config: Config de la fuente
        
    Returns:
        Tupla (metadata_dict, excel_dict) o None si error
        - metadata_dict: Contenido parseado del metadata.json
        - excel_dict: {filename: bytes} de archivos Excel
    """
    # Obtener JSON (metadata)
    json_files = get_latest_raw_files(source_id, source_config)
    if not json_files:
        logger.error(f"[storage] No se encontró metadata para {source_id}")
        return None
    
    # Buscar metadata.json
    metadata_dict = None
    for file_path, content in json_files:
        if 'metadata.json' in file_path:
            try:
                metadata_dict = json.loads(content)
                logger.info(f"[storage] Metadata cargado desde {file_path}")
                break
            except json.JSONDecodeError as e:
                logger.error(f"[storage] Error parseando metadata: {e}")
                return None
    
    if not metadata_dict:
        logger.error(f"[storage] No se encontró metadata.json para {source_id}")
        return None
    
    # Obtener Excel
    excel_files = get_latest_excel_files(source_id, source_config)
    if not excel_files:
        logger.warning(f"[storage] No se encontraron archivos Excel para {source_id}")
        # Retornar metadata sin Excel (puede ser útil para debugging)
        return metadata_dict, {}
    
    return metadata_dict, excel_files


def _group_files_by_timestamp(files: List[str], prefix: str) -> Dict[str, List[str]]:
    """
    Agrupa archivos por timestamp.
    
    Ejemplos de paths:
    - api/api_regalias/2024-11-25_120000.json → timestamp: 2024-11-25_120000
    - api/api_regalias/2024-11-25_120000/page_0001.json → timestamp: 2024-11-25_120000
    - complex/gas/2024-11-25_120000/metadata.json → timestamp: 2024-11-25_120000
    - complex/gas/2024-11-25_120000/excel/res_00739.xlsx → timestamp: 2024-11-25_120000
    """
    files_by_timestamp = {}
    
    for f in files:
        # Remover el prefijo para analizar
        relative_path = f[len(prefix):] if f.startswith(prefix) else f
        parts = relative_path.split('/')
        
        if not parts:
            continue
        
        # El timestamp es el primer componente después del prefijo
        # Puede ser "2024-11-25_120000.json" o "2024-11-25_120000/..."
        first_part = parts[0]
        
        # Extraer timestamp
        if first_part.endswith('.json'):
            timestamp = first_part.rsplit('.', 1)[0]
        else:
            timestamp = first_part
        
        # Validar que parece un timestamp (YYYY-MM-DD_HHMMSS)
        if len(timestamp) >= 10 and '-' in timestamp:
            if timestamp not in files_by_timestamp:
                files_by_timestamp[timestamp] = []
            files_by_timestamp[timestamp].append(f)
    
    return files_by_timestamp


def _download_json_files(
    client: BackendClient, 
    bucket_name: str, 
    file_paths: List[str]
) -> List[Tuple[str, str]]:
    """Descarga archivos JSON y valida su contenido."""
    result = []
    
    for file_path in file_paths:
        try:
            content_bytes = client.download_file(bucket_name, file_path)
            
            if content_bytes is None:
                logger.warning(f"[storage] Archivo vacío o no descargado: {file_path}")
                continue
            
            # Convertir bytes a string
            content_str = content_bytes.decode('utf-8') if isinstance(content_bytes, bytes) else str(content_bytes)
            
            # Validar JSON
            try:
                json.loads(content_str)
            except json.JSONDecodeError as je:
                logger.error(f"[storage] JSON inválido en {file_path}: {je}")
                continue
            
            result.append((file_path, content_str))
            logger.debug(f"[storage] Descargado: {file_path} ({len(content_str)} bytes)")
            
        except Exception as e:
            logger.error(f"[storage] Error descargando {file_path}: {e}")
            continue
    
    return result


def _download_excel_files(
    client: BackendClient, 
    bucket_name: str, 
    file_paths: List[str]
) -> Dict[str, bytes]:
    """
    Descarga archivos Excel y los retorna como diccionario.
    
    Args:
        client: Cliente de backend para acceso a storage
        bucket_name: Nombre del bucket
        file_paths: Lista de paths de archivos Excel
        
    Returns:
        Dict {filename: bytes} con contenido de cada archivo
    """
    result = {}
    
    for file_path in file_paths:
        try:
            content_bytes = client.download_file(bucket_name, file_path)
            
            if content_bytes is None:
                logger.warning(f"[storage] Archivo Excel vacío o no descargado: {file_path}")
                continue
            
            # Extraer nombre de archivo del path (ej: excel/res_00014.xlsm -> res_00014.xlsm)
            filename = file_path.split('/')[-1]
            
            result[filename] = content_bytes
            size_kb = len(content_bytes) / 1024
            logger.info(f"[storage] Excel descargado: {filename} ({size_kb:.1f} KB)")
            
        except Exception as e:
            logger.error(f"[storage] Error descargando Excel {file_path}: {e}")
            continue
    
    return result
