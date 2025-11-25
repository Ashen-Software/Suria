from logs_config.logger import app_logger as logger
from typing import List, Dict, Optional
from .extractors import get_extractor
from .transformers import get_transformer
from services.backend_client import BackendClient


def full_etl_task(changed_sources: List[str], current_config: Dict):
    """
    Recibe la lista de fuentes cambiadas y ejecuta el pipeline ETL:
    1. EXTRACCIÓN: Obtiene datos de la fuente
    2. TRANSFORMACIÓN: Normaliza datos según schema
    3. CARGA: Inserta en PostgreSQL (TODO)
    """
    if not current_config:
        logger.error("[full_etl] No hay config disponible.")
        return

    sources_list = current_config.get("sources", [])
    sources_map = {s["id"]: s for s in sources_list}

    for src_id in changed_sources:
        src = sources_map.get(src_id)
        if not src:
            logger.warning(f"[full_etl] Fuente no encontrada en config: {src_id}")
            continue

        src_type = src.get("type")
        logger.info(f"[full_etl] Iniciando proceso para {src_id} (type={src_type})")

        try:
            # PASO 1: EXTRACCION
            logger.info(f"[full_etl] PASO 1/3: EXTRACCIÓN")
            extractor = get_extractor(src_type)
            if not extractor:
                logger.warning(f"[full_etl] No hay extractor para tipo '{src_type}' en {src_id}")
                continue

            extractor.extract(src)
            logger.info(f"[full_etl] Extracción completada para {src_id}")
            
            # PASO 2: TRANSFORMACION
            logger.info(f"[full_etl] PASO 2/3: TRANSFORMACIÓN")
            transformer = get_transformer(src_type)
            if not transformer:
                logger.warning(f"[full_etl] No hay transformer para tipo '{src_type}' en {src_id}")
                continue
            
            # Obtener archivos RAW mas recientes del storage,
            # pueden ser multiples (lotes con paginacion)
            raw_files = _get_latest_raw_files(src_id, src)
            if not raw_files:
                logger.warning(f"[full_etl] No se encontraron archivos RAW para {src_id}")
                continue
            
            logger.info(f"[full_etl]   Archivos a procesar: {len(raw_files)}")
            
            # Transformar cada archivo y combinar resultados
            transform_result = _transform_multiple_files(raw_files, transformer, src)
            
            valid_count = len(transform_result.get("valid_records", []))
            error_count = len(transform_result.get("errors", []))
            total_raw = transform_result.get("stats", {}).get("total_raw", 0)
            processing_time = transform_result.get("stats", {}).get("processing_time_seconds", 0)
            
            logger.info(f"[full_etl]   Transformación completada:")
            logger.info(f"[full_etl]   - Total RAW: {total_raw}")
            logger.info(f"[full_etl]   - Válidos: {valid_count} ({_pct(valid_count, total_raw):.1f}%)")
            logger.info(f"[full_etl]   - Errores: {error_count} ({_pct(error_count, total_raw):.1f}%)")
            logger.info(f"[full_etl]   - Tiempo: {processing_time:.2f}s")
            
            if error_count > 0:
                error_categories = transform_result.get("stats", {}).get("error_categories", {})
                if error_categories:
                    logger.warning(f"[full_etl] Categorías de error:")
                    for category, count in sorted(error_categories.items(), key=lambda x: x[1], reverse=True):
                        logger.warning(f"[full_etl]   - {category}: {count}")
            
            # TODO: PASO 3: CARGA (Load)
            logger.info(f"[full_etl] PASO 3/3: CARGA (TODO)")
            logger.info(f"[full_etl] {valid_count} registros listos para insertar en PostgreSQL")
            # loader = get_loader(src_type)
            # loader.load(transform_result, src)
            
            logger.info(f"[full_etl] {'='*60}\n")
            
        except Exception as e:
            logger.error(f"[full_etl] Error en proceso ETL de {src_id}: {e}")
            import traceback
            traceback.print_exc()


def _get_latest_raw_files(source_id: str, source_config: Dict) -> Optional[List[tuple]]:
    """
    Obtiene TODOS los archivos RAW del lote más reciente de Storage.
    
    Maneja dos escenarios:
    1. Archivo único: api/{id}/YYYY-MM-DD_HHMMSS.json
    2. Múltiples páginas: api/{id}/YYYY-MM-DD_HHMMSS/page_*.json
    
    Args:
        source_id: ID de la fuente (ej: "api_regalias")
        source_config: Config de la fuente (contiene bucket)
        
    Returns:
        List de tuplas (file_path, content) con los archivos más recientes, o None si error
    """
    try:
        client = BackendClient()
        bucket_name = source_config.get("storage", {}).get("bucket", "raw-data")
        prefix = f"api/{source_id}/"
        
        # Listar archivos en el prefijo
        files = client.list_files(bucket_name, prefix)
        
        if not files:
            logger.warning(f"[full_etl] No hay archivos en {bucket_name}/{prefix}")
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
            logger.warning(f"[full_etl] No se pudieron agrupar archivos por timestamp")
            return None
        
        # Obtener archivos del timestamp mas reciente
        latest_timestamp = sorted(files_by_timestamp.keys())[-1]
        latest_files = sorted(files_by_timestamp[latest_timestamp])
        
        logger.info(f"[full_etl] Lote detectado: {latest_timestamp} con {len(latest_files)} archivo(s)")
        
        # Descargar todos los archivos del lote EN MEMORIA
        result = []
        for file_path in latest_files:
            try:
                # Descargar del bucket (retorna bytes)
                content_bytes = client.download_file(bucket_name, file_path)
                
                if content_bytes is None:
                    logger.warning(f"[full_etl] Archivo vacío o no descargado: {file_path}")
                    continue
                
                # Convertir bytes a string
                if isinstance(content_bytes, bytes):
                    content_str = content_bytes.decode('utf-8')
                else:
                    content_str = str(content_bytes)
                
                # Validar que es JSON valido
                try:
                    import json as json_module
                    json_module.loads(content_str)
                except json_module.JSONDecodeError as je:
                    logger.error(f"[full_etl] Contenido JSON inválido en {file_path}: {je}")
                    continue
                
                result.append((file_path, content_str))
                logger.info(f"[full_etl] Archivo descargado en memoria: {file_path} ({len(content_str)} bytes)")
                
            except Exception as e:
                logger.error(f"[full_etl] Error descargando {file_path}: {e}")
                import traceback
                traceback.print_exc()
                # Continuar con otros archivos
        
        if not result:
            logger.error(f"[full_etl] No se descargó ningún archivo válido para {source_id}")
            return None
        
        return result
        
    except Exception as e:
        logger.error(f"[full_etl] Error obteniendo archivos RAW: {e}")
        import traceback
        traceback.print_exc()
        return None


def _transform_multiple_files(raw_files: List[tuple], transformer, source_config: Dict) -> Dict:
    """
    Transforma múltiples archivos RAW y combina resultados.
    
    IMPORTANTE:
    - Los archivos ya están EN MEMORIA (content_str, no path a disco)
    - Transforma cada uno individualmente
    - Combina: válidos[], errores[], stats (suma + merge)
    
    Args:
        raw_files: List de tuplas (file_path, content_str)
        transformer: Instancia del transformer
        source_config: Config de la fuente
        
    Returns:
        Dict combinado: {valid_records, errors, stats}
    """
    combined_result = {
        "valid_records": [],
        "errors": [],
        "stats": {
            "total_raw": 0,
            "valid": 0,
            "errors": 0,
            "processing_time_seconds": 0,
            "error_categories": {},
            "files_processed": len(raw_files)
        }
    }
    
    import time
    start_time = time.time()
    
    for file_idx, (file_path, raw_data) in enumerate(raw_files, 1):
        logger.info(f"[full_etl] [{file_idx}/{len(raw_files)}] Transformando: {file_path}")
        
        try:
            # Validar que raw_data no esta vacío
            if not raw_data or len(raw_data.strip()) == 0:
                logger.warning(f"[full_etl] Archivo vacío: {file_path}")
                continue
            
            # Ejecutar transformacion
            result = transformer.transform(raw_data, source_config)
            
            if result is None:
                logger.error(f"[full_etl] Transformer retornó None para {file_path}")
                continue
            
            # Agregar resultados
            valid_recs = result.get("valid_records", [])
            errors = result.get("errors", [])
            stats = result.get("stats", {})
            
            logger.debug(f"[full_etl]   → Válidos: {len(valid_recs)}, Errores: {len(errors)}, Total RAW: {stats.get('total_raw', 0)}")
            
            combined_result["valid_records"].extend(valid_recs)
            combined_result["errors"].extend(errors)
            
            # Actualizar stats
            combined_result["stats"]["total_raw"] += stats.get("total_raw", 0)
            combined_result["stats"]["valid"] += stats.get("valid", 0)
            combined_result["stats"]["errors"] += stats.get("errors", 0)
            
            # Mergear error categories
            for category, count in stats.get("error_categories", {}).items():
                combined_result["stats"]["error_categories"][category] = \
                    combined_result["stats"]["error_categories"].get(category, 0) + count
                    
        except Exception as e:
            logger.error(f"[full_etl] Error transformando {file_path}: {e}")
            import traceback
            traceback.print_exc()
            # Continuar con siguientes archivos
    
    combined_result["stats"]["processing_time_seconds"] = time.time() - start_time
    
    logger.info(f"[full_etl] Transformación completa: {combined_result['stats']['files_processed']} archivo(s), "
                f"{combined_result['stats']['total_raw']} registros totales")
    
    return combined_result


def _pct(value: int, total: int) -> float:
    """Calcula porcentaje."""
    if total == 0:
        return 0
    return (value / total) * 100
