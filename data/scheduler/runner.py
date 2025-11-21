from apscheduler.schedulers.background import BackgroundScheduler
import time
import os
from data.logging.logger import app_logger as logger
from data.scheduler.jobs import register_jobs

ENV = os.getenv("APP_ENV", "local")  # "local" | "prod"


def start_scheduler():
    scheduler = BackgroundScheduler()
    
    try:
        register_jobs(scheduler)
        scheduler.start()

        logger.info(f"Scheduler iniciado en entorno: {ENV}")

    except Exception as e:
        logger.error(f"Error iniciando scheduler: {e}")
        scheduler.shutdown(wait=False)
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Deteniendo scheduler manualmente...")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    logger.info("Iniciando runner…")
    start_scheduler()
