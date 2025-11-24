"""
Utilidades para resolver variables de entorno en configuraciones.
Soporta sintaxis $VARIABLE_NAME en strings.
"""

import os
from logs_config.logger import app_logger as logger


def resolve_env_var(value: str) -> str:
    """
    Si un valor comienza con $, lo interpreta como variable de entorno.
    Ejemplo: "$API_TOKEN" -> valor de os.getenv("API_TOKEN")
    """
    if isinstance(value, str) and value.startswith("$"):
        env_var = value[1:]  # Quita el $
        env_value = os.getenv(env_var)
        if env_value is None:
            logger.warning(f"Variable de entorno '{env_var}' no encontrada")
            return value
        return env_value
    return value


def resolve_dict_env_vars(obj):
    """
    Resuelve variables de entorno en todos los valores de una estructura recursivamente.
    Soporta dicts, lists y strings.
    """
    if isinstance(obj, dict):
        return {k: resolve_dict_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_dict_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        return resolve_env_var(obj)
    else:
        return obj
