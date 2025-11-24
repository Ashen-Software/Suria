# Guía de Configuración de Fuentes y Storage

Esta guía detalla cómo configurar el almacenamiento en Supabase y la vinculación de scripts personalizados para las fuentes de datos en el sistema ETL.

## 1. Supabase Storage

El sistema utiliza Supabase Storage para almacenar la data cruda (RAW) extraída de las diferentes fuentes.

### Creación del Bucket
Para que el sistema funcione correctamente, se debe crear un bucket en el proyecto de Supabase con las siguientes características:

*   **Nombre del Bucket:** `raw-data`
*   **Acceso:** Privado (recomendado) o Público.

### Estructura de Archivos
El sistema organiza automáticamente los archivos descargados para mantener un historial ordenado cronológicamente. La estructura de carpetas generada por defecto es:

```text
{tipo_fuente}/{id_fuente}/{YYYY-MM-DD_HHMMSS}.{ext}
```

**Ejemplos:**
*   `api/api_gas/2023-11-24_103000.json`
*   `web/noticias_col/2023-11-24_154500.html`
*   `complex/banco_central/2023-11-24_090000.bin`

Esta estructura plana facilita la gestión de historiales cortos (ej. últimos 2-3 meses).

---

## 2. Configuración en `sources_config.json`

Cada fuente en `etl_sources` (o `sources_config.json`) tiene una sección `storage` para definir dónde se guardan los datos.

### Configuración Básica
Solo es necesario especificar el nombre del bucket. El sistema se encarga de generar la ruta y el nombre del archivo.

```json
{
  "id": "mi_fuente",
  "type": "api",
  "storage": {
    "bucket": "raw-data"
  }
}
```

### Parámetros Disponibles

| Parámetro | Descripción | Valor por defecto |
| :--- | :--- | :--- |
| `bucket` | Nombre del bucket en Supabase. | `"raw-data"` |
| `path` | (Opcional) Ruta completa del archivo. Si se define, **sobrescribe** la generación automática de historial. Útil si solo se desea mantener la última versión. | `None` (Automático) |

---

## 3. Scripts Personalizados (`complex_scraper`)

Para fuentes que requieren lógica de extracción compleja (Selenium, Playwright, pasos múltiples), se utiliza el tipo `complex_scraper`.

### Vinculación del Script
El sistema busca un script de Python en la carpeta `data/extraction/scrapers/`. Por defecto, busca un archivo con el mismo nombre que el `id` de la fuente.

Para usar un nombre de archivo diferente, se utiliza el parámetro `script_name` dentro de `config`.

**Ejemplo de Configuración:**

```json
{
  "id": "banco_central_trm",
  "type": "complex_scraper",
  "config": {
    "script_name": "bot_banco_central" 
  },
  "storage": {
    "bucket": "raw-data"
  }
}
```

En este caso:
1.  El sistema buscará el archivo `data/extraction/scrapers/bot_banco_central.py`.
2.  Ejecutará la función `extract(config)` definida en ese archivo.
3.  El script debe retornar el contenido del archivo (bytes o string).
4.  El sistema guardará ese contenido en `raw-data/complex/banco_central_trm/YYYY-MM-DD_HHMMSS.bin`.
