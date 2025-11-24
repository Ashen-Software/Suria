from typing import Dict, Any
import random

def check(source_config: Dict[str, Any]) -> str:
    """
    Ejemplo de lógica custom para una fuente específica.
    Aqui se configura el scraper especifico: Selenium, Playwright, u otra logica.
    (ej. validar que hoy es día hábil antes de chequear).
    """
    # Simulación: Retorna un valor que cambia aleatoriamente para probar detección
    # En la vida real: return driver.find_element(...).text
    return f"custom_value_{random.randint(1, 100)}"

def extract(source_config: Dict[str, Any]) -> bytes:
    """
    Ejemplo de extracción custom.
    Retorna el contenido del archivo a subir.
    """
    return b"Contenido de ejemplo del scraper custom"
