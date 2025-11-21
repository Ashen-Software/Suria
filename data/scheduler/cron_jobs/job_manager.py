import json
import os
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from data.logging.logger import app_logger as logger

CONFIG_PATH = Path(__file__).resolve().parent.parent / "workflows" / "sources_config.json"
ENV = os.getenv("APP_ENV", "local")  # "local" | "prod"


def load_local_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            logger.info("Cargando configuración desde archivo local.")
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando config local: {e}")
        return []


def load_remote_config():
    """
    Placeholder para producción.
    Aquí consultaremos Supabase o una API interna.
    """
    try:
        logger.info("Cargando configuración desde Supabase...")
        
        # TODO
        # from supabase import create_client
        # supabase = create_client(URL, KEY)
        # res = supabase.table("sources").select("*").execute()
        # return res.data

        return []
    except Exception as e:
        logger.error(f"Error obteniendo configuración remota: {e}")
        return []


def load_sources_config():
    """
    Decide si cargar config desde archivo o desde Supabase.
    """
    if ENV == "prod":
        config = load_remote_config()
        if config:
            return config
        logger.warning("Fallo remoto, usando config local como fallback.")
    
    return load_local_config()


def run_check_updates(source):
    """
    Ejecuta accion por fuente.
    """
    from data.workflows.check_updates import run as check_updates_run

    logger.info(f"Ejecutando check_updates para: {source['id']}")
    check_updates_run(source)


def register_jobs(scheduler: BackgroundScheduler):
    sources = load_sources_config()

    if not sources:
        logger.warning("No hay fuentes configuradas. Scheduler no creará jobs.")
        return

    for src in sources:
        cron_expr = src.get("schedule", {}).get("cron", "0 0 * * 0")
        job_id = f"check_updates_{src['id']}"

        scheduler.add_job(
            run_check_updates,
            trigger=CronTrigger.from_crontab(cron_expr),
            args=[src],
            id=job_id,
            replace_existing=True
        )

        logger.info(f"Job registrado: {job_id} | cron={cron_expr}")

    logger.info(f"Total jobs creados: {len(sources)}")
