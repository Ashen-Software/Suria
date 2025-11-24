# Guía de Configuración de Fuentes

Esta guía proporciona una introducción a cómo configurar diferentes tipos de fuentes de datos en el sistema ETL.

## Tipos de Fuentes Soportadas

| Tipo | Descripción | Complejidad | Ejemplo |
|------|-------------|-------------|---------|
| `api` | Consume datos directamente de una API REST | Baja | API de datos públicos, Socrata |
| `web` | Descarga HTML de un sitio web | Baja | Web scraping básico |
| `complex_scraper` | Lógica personalizada con Selenium/Playwright | Alta | Navegación interactiva, JS renderizado |

## Guías Específicas

Para detalles completos sobre cada tipo de configuración, consulta:

- **[Configuración de Storage](storage_configuracion.md)** - Dónde se guardan los datos
- **[Configuración de APIs](api_configuracion.md)** - Cómo consumir APIs REST
- **[Scripts Personalizados](scripts_personalizados.md)** - Implementar lógica compleja

## Estructura Básica de una Fuente

```json
{
  "id": "mi_fuente",
  "name": "Mi Fuente de Datos",
  "active": true,
  "type": "api",
  "schedule": { "cron": "0 9 * * *", "note": "Daily at 9 AM" },
  "config": {
    // Configuración específica del tipo
  },
  "storage": {
    "bucket": "raw-data"
  }
}
```

### Parámetros Comunes

| Parámetro | Descripción | Requerido |
|-----------|-------------|-----------|
| `id` | Identificador único de la fuente | Sí |
| `name` | Nombre descriptivo | No |
| `active` | Si debe ejecutarse | Sí |
| `type` | Tipo de fuente: `api`, `web`, `complex_scraper` | Sí |
| `schedule` | Cron de ejecución | Sí |
| `config` | Configuración específica del tipo | Sí |
| `storage` | Dónde guardar los datos | Sí |

### Formatos de Schedule (cron)

```json
"schedule": { 
  "cron": "0 9 * * *",
  "note": "Daily at 9 AM"
}
```

Ejemplos comunes:
- `"* * * * *"` - Cada minuto
- `"0 * * * *"` - Cada hora
- `"0 9 * * *"` - Cada día a las 9 AM
- `"0 0 * * 1"` - Cada lunes a medianoche
- `"*/30 * * * *"` - Cada 30 minutos

## Flujo de Ejecución

### 1. Scheduler
El APScheduler ejecuta según el cron definido.

### 2. Check Updates (Detección de Cambios)
- Resuelve variables de entorno
- Consulta estado actual (metadata o datos)
- Calcula hash SHA256
- Compara con última ejecución

### 3. Decisión
- **Cambios detectados** → Ejecuta Full ETL
- **Sin cambios** → Omite descarga

### 4. Full ETL (Si hay cambios)
- Resuelve variables de entorno
- Descarga/procesa datos
- Genera ruta con timestamp
- Sube archivo a Supabase Storage

### 5. Registro en Base de Datos
- `etl_sources`: estado y última verificación
- `source_check_history`: historial de cada ejecución

## Mejores Prácticas

- Mantén credenciales en `.env`, nunca en config
- Usa `$VARIABLE` para referencias a variables de entorno
- Aprovecha `check_endpoint` para APIs grandes (reduce transferencia)
- Define schedules apropiados (no sobrecargar servicios)
- Registra cambios en Git, no datos descargados
- Nunca commitees `.env` con credenciales reales

## Ejemplos Completos

### Ejemplo 1: API Simple
```json
{
  "id": "api_gas",
  "name": "API Gas Colombia",
  "active": true,
  "type": "api",
  "schedule": { "cron": "0 * * * *" },
  "config": {
    "base_url": "https://httpbin.org/json"
  },
  "storage": { "bucket": "raw-data" }
}
```

### Ejemplo 2: API con Autenticación
```json
{
  "id": "api_regalias",
  "name": "Consolidación de regalias",
  "active": true,
  "type": "api",
  "schedule": { "cron": "0 9 * * *" },
  "config": {
    "base_url": "https://www.datos.gov.co/api/v3/views/j7js-yk74/query.json",
    "check_endpoint": "https://www.datos.gov.co/api/views/j7js-yk74.json",
    "check_field": "rowsUpdatedAt",
    "params": { "app_token": "$DATOS_GOV_TOKEN" },
    "headers": { "Accept": "application/json" }
  },
  "storage": { "bucket": "raw-data" }
}
```

### Ejemplo 3: Web Scraping
```json
{
  "id": "scrape_example",
  "name": "Scrape Example",
  "active": true,
  "type": "web",
  "schedule": { "cron": "0 12 * * *" },
  "config": { "url": "https://example.com" },
  "storage": { "bucket": "raw-data" }
}
```

### Ejemplo 4: Script Personalizado
```json
{
  "id": "banco_central",
  "name": "Banco Central Bot",
  "active": true,
  "type": "complex_scraper",
  "schedule": { "cron": "0 9 * * *" },
  "config": { "script_name": "bot_banco_central" },
  "storage": { "bucket": "raw-data" }
}
```

---

## Archivos de Referencia

- `data/workflows/sources_config.json` - Configuración de ejemplo
- `data/extraction/scrapers/` - Ubicación de scripts personalizados
- `docs/database/esquema.md` - Esquema de base de datos
