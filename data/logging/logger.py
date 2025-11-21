import os
import logging
from loguru import logger

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
SERVICE_NAME = os.getenv("SERVICE_NAME", "etl_service")

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE_PATH = os.path.join(LOG_DIR, "runtime.log")

# Crear carpeta si no existe
os.makedirs(LOG_DIR, exist_ok=True)


def configure_logger():
    """
    Configura Loguru para:
    - Logs JSON en producción
    - Logs legibles en desarrollo
    - Logs rotados en archivo persistente
    """

    # Limpiar handlers previos
    logger.remove()

    # LOG A CONSOLA
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=LOG_LEVEL,
        serialize=(LOG_ENVIRONMENT == "prod"),
        backtrace=True,
        diagnose=(LOG_ENVIRONMENT == "dev"),
    )

    # LOG A ARCHIVO
    logger.add(
        LOG_FILE_PATH,
        level=LOG_LEVEL,
        serialize=(LOG_ENVIRONMENT == "prod"),
        rotation="10 MB",
        retention="10 days",
        backtrace=True,
        diagnose=(LOG_ENVIRONMENT == "dev"),
    )

    logger.info(f"Logger configurado | environment={LOG_ENVIRONMENT} | service={SERVICE_NAME}")
    return logger


# Instancia global para importar desde otros módulos
app_logger = configure_logger()
