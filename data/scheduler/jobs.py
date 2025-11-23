import os
import json
from pathlib import Path
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler

from logs_config.logger import app_logger as logger
from services.config_manager import ConfigManager
import settings


ENV = settings.ENVIRONMENT


def get_sources():
    """
    Usa ConfigManager en prod o si se fuerza remoto, cache local en dev.
    """

    use_remote = settings.USE_REMOTE_CONFIG
    # print(os.getenv("USE_REMOTE_CONFIG")) # Debug line removed
    
    if ENV == "prod" or use_remote:
        try:
            cfg = ConfigManager().get_config()
            return cfg.get("sources", [])
        except Exception as e:
            logger.error("remote_config_error", error=str(e))
            # Si estamos forzando remoto en dev y falla, volver al local
            if not use_remote: 
                return []

    # Local: lee archivo local sin Supabase
    local_path = Path(__file__).resolve().parent.parent / "workflows" / "sources_config.json"

    if not local_path.exists():
        logger.error("config_not_found", path=str(local_path))
        return []

    logger.debug("using_local_config", path=str(local_path))
    
    with open(local_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    return config.get("sources", [])


def run_check_updates(source):
    src_id = source.get('id')
    src_name = source.get('name', src_id)

    logger.info("check_updates_started", source_id=src_id, source_name=src_name)

    try:
        from workflows.check_updates.run import check_updates_task
        from workflows.full_etl.run import full_etl_task

        # check_updates_task espera el config completo, creamos uno con solo esta fuente
        temp_config = {"sources": [source]}
        changed_sources = check_updates_task(temp_config)

        if changed_sources:
            logger.info("changes_detected", source_id=src_id, changed_count=len(changed_sources))
            logger.info("full_etl_started", source_id=src_id)

            full_etl_task(changed_sources, temp_config)

            logger.info("full_etl_completed", source_id=src_id)
        else:
            logger.info("no_changes", source_id=src_id)

    except Exception as e:
        # Capturar cualquier excepcion durante la ejecución del job para
        # evitar que una excepción no manejada afecte al scheduler.
        logger.error("run_check_updates_failed", source_id=src_id, error=str(e), exc_info=True)


def register_jobs(scheduler: BackgroundScheduler):
    """Registra jobs iniciales desde config"""
    sources = get_sources()

    if not sources:
        logger.warning("empty_config")
        return

    logger.info("registering_jobs", total_sources=len(sources))
    registered_count = 0
    
    for src in sources:
        src_id = src.get('id')
        src_name = src.get('name', src_id)
        is_active = src.get("active", False)
        
        if not is_active:
            logger.debug("source_inactive", source_id=src_id, source_name=src_name)
            continue

        cron_expr = src.get("schedule", {}).get("cron", "0 0 * * 0")
        job_id = f"check_updates_{src_id}"

        try:
            scheduler.add_job(
                run_check_updates,
                trigger=CronTrigger.from_crontab(cron_expr),
                args=[src],
                id=job_id,
                replace_existing=True
            )
            logger.info("job_registered", source_id=src_id, source_name=src_name, cron=cron_expr)
            registered_count += 1

        except Exception as e:
            logger.error("job_registration_failed", source_id=src_id, error=str(e), exc_info=True)

    if registered_count == 0 and len(sources) > 0:
        logger.warning("all_sources_inactive", message="Todas las fuentes están apagadas -> el proceso se considera detenido")
    
    logger.info("jobs_registered", registered=registered_count, total=len(sources))


def reload_jobs_if_changed(scheduler: BackgroundScheduler):
    """
    Recarga el config y sincroniza jobs basandose en id y active.
    - Si source.active=true y no existe el job -> lo crea
    - Si source.active=true y existe el job -> lo actualiza (por si cambio cron u otros params)
    - Si source.active=false o fue removido del config -> elimina el job
    """
    logger.debug("reloading_config")
    
    # Leer config fresco
    current_sources = get_sources()
    
    # Crear mapeo de sources actuales por ID
    current_map = {s['id']: s for s in current_sources}
    current_active_ids = {s['id'] for s in current_sources if s.get('active', False)}
    
    # Obtener todos los jobs actuales del scheduler (solo check_updates)
    existing_jobs = {job.id: job for job in scheduler.get_jobs() if job.id.startswith('check_updates_')}
    existing_job_ids = {job_id.replace('check_updates_', '') for job_id in existing_jobs.keys()}
    
    logger.debug("config_state", 
                 total_sources=len(current_sources),
                 active_sources=list(current_active_ids),
                 existing_jobs=list(existing_job_ids))
    
    # Eliminar jobs que ya no estan activos o fueron removidos del config
    for job_id in list(existing_jobs.keys()):
        src_id = job_id.replace('check_updates_', '')
        
        # Si el source ya no existe o esta inactivo, remover job
        if src_id not in current_active_ids:
            scheduler.remove_job(job_id)
            reason = 'removed_from_config' if src_id not in current_map else 'deactivated'
            logger.info("job_removed", source_id=src_id, reason=reason)
    
    # Agregar o actualizar jobs para sources activos
    for src_id in current_active_ids:
        src = current_map[src_id]
        src_name = src.get('name', src_id)
        cron_expr = src.get("schedule", {}).get("cron", "0 0 * * 0")
        job_id = f"check_updates_{src_id}"
        
        try:
            # replace_existing=True actualiza si existe, crea si no existe
            scheduler.add_job(
                run_check_updates,
                trigger=CronTrigger.from_crontab(cron_expr),
                args=[src],
                id=job_id,
                replace_existing=True
            )
            
            action = "updated" if job_id in existing_jobs else "added"
            logger.info("job_synced", source_id=src_id, source_name=src_name, action=action, cron=cron_expr)
            
        except Exception as e:
            logger.error("job_sync_failed", source_id=src_id, error=str(e), exc_info=True)
    
    active_count = len(current_active_ids)
    
    if active_count == 0 and len(current_sources) > 0:
        logger.warning("all_sources_inactive", message="Todas las fuentes están apagadas: el proceso se considera detenido")
    
    logger.info("config_reloaded", active_jobs=active_count)
