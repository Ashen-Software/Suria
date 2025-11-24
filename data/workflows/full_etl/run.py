from logs_config.logger import app_logger as logger
from typing import List, Dict
from .extractors import get_extractor

def full_etl_task(changed_sources: List[str], current_config: Dict):
    """
    Recibe la lista de fuentes cambiadas y ejecuta la extracción por cada una.
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

        extractor = get_extractor(src_type)
        if not extractor:
            logger.warning(f"[full_etl] No hay extractor para tipo '{src_type}' en {src_id}")
            continue

        try:
            extractor.extract(src)
            logger.info(f"[full_etl] Extracción finalizada para {src_id}")
            
            # TODO: Aquí seguirían los pasos de Transformación y Carga (Load)
            # transformer = get_transformer(src_type)
            # transformer.transform(...)
            
        except Exception as e:
            logger.error(f"[full_etl] Error en proceso ETL de {src_id}: {e}")
