import time
import logging
import settings

from logs_config.logger import app_logger as logger
from scheduler.jobs import register_jobs, reload_jobs_if_changed
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

ENV = settings.ENVIRONMENT
CONFIG_RELOAD_INTERVAL = settings.CONFIG_RELOAD_INTERVAL


def start_scheduler():
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    
    # Configurar un executor de hilos y defaults de job para evitar
    # que tareas pesadas bloqueen la recarga y para controlar instancias
    executors = {
        'default': ThreadPoolExecutor(10),
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 2,
        'misfire_grace_time': 60,
    }

    scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults)
    
    logger.info("scheduler_starting", environment=ENV)
    
    try:
        # Registrar jobs iniciales
        register_jobs(scheduler)
        
        # Refresher
        scheduler.add_job(
            reload_jobs_if_changed,
            trigger=IntervalTrigger(seconds=CONFIG_RELOAD_INTERVAL),
            args=[scheduler],
            id="reload_config_job",
            replace_existing=True,
            max_instances=1,
            coalesce=False,
            misfire_grace_time=60,
        )
        logger.info("config_reloader_registered", interval_seconds=CONFIG_RELOAD_INTERVAL)
        
        scheduler.start()
        logger.info("scheduler_started", environment=ENV)

    except Exception as e:
        logger.error("scheduler_start_failed", error=str(e), exc_info=True)
        scheduler.shutdown(wait=False)
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("scheduler_shutdown", reason="user_interrupt")
        scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")


if __name__ == "__main__":
    start_scheduler()
