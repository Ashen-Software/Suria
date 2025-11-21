import os
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler

from data.logging.logger import app_logger as logger
from data.services.config_manager import ConfigManager


ENV = os.getenv("APP_ENV", "local")


def get_sources():
    """
    Usa ConfigManager en prod, cache local en dev.
    """
    if ENV == "prod":
        cfg = ConfigManager().get_config()
        return cfg.get("sources", [])

    # Local: lee archivo cacheado o local sin Supabase
    from pathlib import Path
    import json

    local_path = Path(__file__).resolve().parent.parent / "workflows" / "sources_config.json"

    if not local_path.exists():
        logger.error("No se encontró sources_config.json en local.")
        return []

    logger.info("Usando configuración local desde sources_config.json")

    return json.loads(local_path.read_text()).get("sources", [])


def run_check_updates(source):
    from data.workflows.check_updates.run import run as check_updates_run
    logger.info(f"Ejecutando check_updates para la fuente: {source['id']}")
    check_updates_run(source)


def register_jobs(scheduler: BackgroundScheduler):
    sources = get_sources()

    if not sources:
        logger.warning("No se registrará ningún job (config vacía).")
        return

    for src in sources:
        cron_expr = src.get("schedule", {}).get("cron", "0 0 * * 0")
        job_id = f"check_updates_{src['id']}"

        try:
            scheduler.add_job(
                run_check_updates,
                trigger=CronTrigger.from_crontab(cron_expr),
                args=[src],
                id=job_id,
                replace_existing=True
            )
            logger.info(f"Job registrado: {job_id} | cron={cron_expr}")

        except Exception as e:
            logger.error(
                f"Error registrando job para {src['id']} | cron={cron_expr} | error={e}"
            )

    logger.success(f"Total jobs registrados: {len(sources)}")
