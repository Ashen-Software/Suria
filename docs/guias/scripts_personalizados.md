# Configuración de Scripts Personalizados

Para fuentes que requieren lógica de extracción compleja (Selenium, Playwright, pasos múltiples), se utiliza el tipo `complex_scraper`.

## Vinculación del Script

El sistema busca un script de Python en la carpeta `data/extraction/scrapers/`. Por defecto, busca un archivo con el mismo nombre que el `id` de la fuente.

Para usar un nombre de archivo diferente, se utiliza el parámetro `script_name` dentro de `config`.

## Ejemplo Básico

```json
{
  "id": "banco_central_trm",
  "type": "complex_scraper",
  "schedule": { "cron": "0 9 * * *" },
  "config": {
    "script_name": "bot_banco_central"
  },
  "storage": {
    "bucket": "raw-data"
  }
}
```

En este ejemplo:
- El sistema buscará `data/extraction/scrapers/bot_banco_central.py`
- Ejecutará la función `check(config)` durante la detección de cambios
- Ejecutará la función `extract(config)` durante la descarga

## Estructura del Script Personalizado

El script debe implementar dos funciones:

### Función `check(config)`

Realiza la detección de cambios. Debe retornar un valor hasheable (string, número, etc).

```python
def check(source_config: Dict[str, Any]) -> str:
    """
    Detecta cambios en la fuente.
    Retorna un valor que será hasheado para comparar con ejecuciones anteriores.
    
    Ejemplos:
    - Timestamp del último cambio
    - Hash de contenido visible
    - Número de elementos en la página
    """
    # Usar Selenium/Playwright para obtener información
    # ...
    return f"estado_actual_{timestamp}"
```

### Función `extract(config)`

Realiza la extracción de datos. Debe retornar bytes o string con el contenido.

```python
def extract(source_config: Dict[str, Any]) -> bytes:
    """
    Descarga y procesa los datos.
    Retorna el contenido a guardar en Storage.
    """
    # Usar Selenium/Playwright para descargar/procesar datos
    # ...
    return contenido_procesado.encode('utf-8')
```

## Ejemplo Real: Bot del Banco Central

```python
# data/extraction/scrapers/bot_banco_central.py

from typing import Dict, Any
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

def check(source_config: Dict[str, Any]) -> str:
    """Detecta si hubo cambios en la tasa representativa del mercado."""
    driver = webdriver.Chrome()
    try:
        driver.get("https://www.bancocentral.gov.co/tasas")
        
        # Extrae el timestamp de última actualización
        update_element = driver.find_element(By.CLASS_NAME, "last-update")
        last_update = update_element.text
        
        return last_update
    finally:
        driver.quit()

def extract(source_config: Dict[str, Any]) -> bytes:
    """Descarga la tasa actual."""
    driver = webdriver.Chrome()
    try:
        driver.get("https://www.bancocentral.gov.co/tasas")
        
        # Espera a que cargue la tasa
        rate_element = driver.find_element(By.ID, "current-rate")
        rate = rate_element.text
        
        # Procesa y retorna
        data = f"TRM: {rate} - {datetime.now().isoformat()}"
        return data.encode('utf-8')
    finally:
        driver.quit()
```

## Variables de Entorno en Scripts

También puedes usar variables de entorno dentro de scripts personalizados:

```python
import os
from common.env_resolver import resolve_env_var

def check(source_config: Dict[str, Any]) -> str:
    # Resuelve variable de entorno
    api_token = resolve_env_var("$MY_SECRET_TOKEN")
    
    # O acceso directo
    api_token = os.getenv("MY_SECRET_TOKEN")
    
    # ... resto del código
```

## Recomendaciones

- Usa try/finally para cerrar drivers (Selenium/Playwright)
- Implementa timeouts en las búsquedas de elementos
- Registra errores con el logger

## Depuración Local

Para probar tu script sin el scheduler:

```python
# test_bot_banco_central.py
from extraction.scrapers.bot_banco_central import check, extract

config = {
    "id": "banco_central_trm",
    "config": {}
}

# Prueba check
print("Check:", check(config))

# Prueba extract
print("Extract:", extract(config))
```
