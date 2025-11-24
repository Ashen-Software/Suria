# Configuración de Storage

El sistema utiliza Supabase Storage para almacenar la data cruda (RAW) extraída de las diferentes fuentes.

## Creación del Bucket

Para que el sistema funcione correctamente, se debe crear un bucket en el proyecto de Supabase con las siguientes características:

*   **Nombre del Bucket:** `raw-data`
*   **Acceso:** Privado (recomendado) o Público.

## Estructura de Archivos

El sistema organiza automáticamente los archivos descargados para mantener un historial ordenado cronológicamente. La estructura de carpetas generada por defecto es:

```text
{tipo_fuente}/{id_fuente}/{YYYY-MM-DD_HHMMSS}.{ext}
```

**Ejemplos:**
*   `api/api_gas/2023-11-24_103000.json`
*   `web/noticias_col/2023-11-24_154500.html`
*   `complex/banco_central/2023-11-24_090000.bin`

Esta estructura plana facilita la gestión de historiales cortos (ej. últimos 2-3 meses).

## Configuración Básica

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

## Parámetros Disponibles

| Parámetro | Descripción | Valor por defecto |
| :--- | :--- | :--- |
| `bucket` | Nombre del bucket en Supabase. | `"raw-data"` |
| `path` | (Opcional) Ruta completa del archivo. Si se define, **sobrescribe** la generación automática de historial. Útil si solo se desea mantener la última versión. | `None` (Automático) |

**Nota:** Para historiales, es recomendable omitir `path` y dejar que el sistema genere la ruta con timestamp automáticamente.
