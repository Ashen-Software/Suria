from logs_config.logger import app_logger as logger
from typing import List, Dict, Optional
from .extractors import get_extractor
from .transformers import get_transformer
from .loaders import FactLoader
from .storage import get_latest_raw_files
from .pipeline import transform_multiple_files, success_percentage


def full_etl_task(changed_sources: List[str], current_config: Dict, skip_load: bool = False):
    """
    Recibe la lista de fuentes cambiadas y ejecuta el pipeline ETL:
    1. EXTRACCIÓN: Obtiene datos de la fuente
    2. TRANSFORMACIÓN: Normaliza datos según schema
    3. CARGA: Inserta en PostgreSQL
    
    Args:
        changed_sources: Lista de IDs de fuentes a procesar
        current_config: Configuración con fuentes
        skip_load: Si True, omite el paso de carga (útil para pruebas)
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
            breakpoint()
            
            # PASO 2: TRANSFORMACION
            logger.info(f"[full_etl] PASO 2/3: TRANSFORMACIÓN")
            transformer = get_transformer(src_type)
            if not transformer:
                logger.warning(f"[full_etl] No hay transformer para tipo '{src_type}' en {src_id}")
                continue
            
            # Obtener archivos RAW mas recientes del storage,
            # pueden ser multiples (lotes con paginacion)
            raw_files = get_latest_raw_files(src_id, src)
            if not raw_files:
                logger.warning(f"[full_etl] No se encontraron archivos RAW para {src_id}")
                continue
            
            logger.info(f"[full_etl]   Archivos a procesar: {len(raw_files)}")
            
            # Transformar cada archivo y combinar resultados
            transform_result = transform_multiple_files(raw_files, transformer, src)
            
            valid_count = len(transform_result.get("valid_records", []))
            error_count = len(transform_result.get("errors", []))
            total_raw = transform_result.get("stats", {}).get("total_raw", 0)
            processing_time = transform_result.get("stats", {}).get("processing_time_seconds", 0)
            
            logger.info(f"[full_etl]   Transformación completada:")
            logger.info(f"[full_etl]   - Total RAW: {total_raw}")
            logger.info(f"[full_etl]   - Válidos: {valid_count} ({success_percentage(valid_count, total_raw):.1f}%)")
            logger.info(f"[full_etl]   - Errores: {error_count} ({success_percentage(error_count, total_raw):.1f}%)")
            logger.info(f"[full_etl]   - Tiempo: {processing_time:.2f}s")
            
            if error_count > 0:
                error_categories = transform_result.get("stats", {}).get("error_categories", {})
                if error_categories:
                    logger.warning(f"[full_etl] Categorías de error:")
                    for category, count in sorted(error_categories.items(), key=lambda x: x[1], reverse=True):
                        logger.warning(f"[full_etl]   - {category}: {count}")
            
            # PASO 3: CARGA (Load)
            logger.info(f"[full_etl] PASO 3/3: CARGA")
            
            valid_records = transform_result.get("valid_records", [])
            
            if skip_load:
                logger.info(f"[full_etl] Carga omitida (skip_load=True). {valid_count} registros listos.")
            elif valid_count == 0:
                logger.warning(f"[full_etl] No hay registros válidos para cargar")
            else:
                # Determinar fact_table del primer registro (para logging)
                fact_table = valid_records[0].get("fact_table", "unknown") if valid_records else "unknown"
                logger.info(f"[full_etl]   Destino: {fact_table}")
                logger.info(f"[full_etl]   Registros a cargar: {valid_count}")
                
                # FactLoader es generico: maneja cualquier fact_table configurada
                loader = FactLoader(batch_size=10000)
                load_result = loader.load(valid_records, src_id)
                
                load_stats = load_result.get("stats", {})
                logger.info(f"[full_etl]   Carga completada:")
                logger.info(f"[full_etl]   - Upserted: {load_stats.get('inserted', 0)}")
                logger.info(f"[full_etl]   - Duplicados removidos: {load_stats.get('duplicates_in_batch', 0)}")
                logger.info(f"[full_etl]   - Sin tiempo_id: {load_stats.get('skipped_no_tiempo', 0)}")
                logger.info(f"[full_etl]   - Sin campo_id: {load_stats.get('skipped_no_campo', 0)}")
                logger.info(f"[full_etl]   - Errores: {load_stats.get('errors', 0)}")
                
                # Mostrar stats del resolver
                resolver_stats = load_result.get("resolver_stats", {})
                if resolver_stats:
                    logger.debug(f"[full_etl]   Resolver stats: {resolver_stats}")
                
                if load_result.get("status") == "error":
                    logger.error(f"[full_etl] Carga falló para {src_id}")
                    error_details = load_result.get("error_details", [])
                    for err in error_details[:5]:  # Mostrar primeros 5 errores
                        logger.error(f"[full_etl]   {err}")
            
            logger.info(f"[full_etl] {'='*60}\n")
            
        except Exception as e:
            logger.error(f"[full_etl] Error en proceso ETL de {src_id}: {e}")
            import traceback
            traceback.print_exc()

