# Configuración de APIs

El sistema soporta múltiples métodos de autenticación y optimizaciones para consultas a APIs.

## Variables de Entorno

Cualquier valor en `params` o `headers` que comience con `$` es tratado como una variable de entorno. Esto permite mantener las credenciales seguras sin exponerlas en el código.

**Sintaxis:**
```json
"$VARIABLE_NAME"  → se resuelve como os.getenv("VARIABLE_NAME")
```

**Ejemplo:**
```json
{
  "id": "api_regalias",
  "type": "api",
  "config": {
    "base_url": "https://www.datos.gov.co/api/v3/views/j7js-yk74/query.json",
    "params": {
      "app_token": "$DATOS_GOV_TOKEN"
    },
    "headers": {
      "Accept": "application/json"
    }
  }
}
```

En el archivo `.env`:
```env
DATOS_GOV_TOKEN=tu_token_aqui
```

## Tipos de Autenticación

El parámetro `auth_type` en `config` especifica el método de autenticación. La credencial se define mediante `auth_key_env` (nombre de la variable de entorno).

| auth_type | Descripción | Ejemplo |
|-----------|-------------|---------|
| `bearer` | Agrega header `Authorization: Bearer {token}` | OAuth 2.0, APIs modernas |
| `api_key` | Agrega header `X-API-Key: {token}` | APIs que usan API Keys |
| `custom_header` | Permite especificar el nombre del header | Cualquier header personalizado |

**Ejemplo con Bearer Token:**
```json
{
  "id": "api_ejemplo",
  "type": "api",
  "config": {
    "base_url": "https://api.ejemplo.com/data",
    "auth_type": "bearer",
    "auth_key_env": "API_EJEMPLO_TOKEN",
    "headers": { "Accept": "application/json" }
  }
}
```

En `.env`:
```env
API_EJEMPLO_TOKEN=sk_live_xxxxx
```

## Detección Eficiente de Cambios (APIs Socrata)

Para APIs que retornan grandes volúmenes de datos (ej. 200K+ registros), es ineficiente descargar todo para detectar cambios. Socrata y plataformas similares exponen un endpoint de **metadata** mucho más ligero.

### Parámetros especiales

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `check_endpoint` | Endpoint de metadata (sin datos) | `https://datos.gov.co/api/views/{id}.json` |
| `check_field` | Campo en la metadata que indica cambios | `rowsUpdatedAt`, `lastUpdateTime` |

### Flujo optimizado

1. **Check** → Consulta solo metadata (~5KB)
2. Compara el campo `check_field` con la ejecución anterior
3. **Si cambió** → Ejecuta Full ETL y descarga los datos
4. **Si no cambió** → Omite la descarga (ahorro de ancho de banda)

### Ejemplo de Configuración

```json
{
  "id": "api_regalias",
  "type": "api",
  "config": {
    "base_url": "https://www.datos.gov.co/api/v3/views/j7js-yk74/query.json",
    "check_endpoint": "https://www.datos.gov.co/api/views/j7js-yk74.json",
    "check_field": "rowsUpdatedAt",
    "params": {
      "app_token": "$DATOS_GOV_TOKEN"
    },
    "headers": {
      "Accept": "application/json"
    }
  }
}
```

## Paginación de Datos Extensos

Para APIs que retornan muy grandes volúmenes de datos (ej. 500K+ registros), el sistema soporta descarga **paginada automática**. Cada página se guarda en un archivo separado para evitar timeouts y saturación de memoria.

### Cuándo usar paginación

- Dataset > 100K registros
- API soporta parámetros de paginación
- Necesitas descarga robusta y recuperable por páginas

### Tipos de Paginación Soportados

#### 1. **Page-based** (Socrata, muchas APIs modernas)
Usa `pageNumber` y `pageSize`

```json
{
  "pagination": {
    "enabled": true,
    "page_param": "pageNumber",
    "size_param": "pageSize",
    "page_size": 10000
  }
}
```

**URL generada:**
```
https://api.datos.gov.co/data?pageNumber=1&pageSize=10000&app_token=XXX
https://api.datos.gov.co/data?pageNumber=2&pageSize=10000&app_token=XXX
...
```

#### 2. **Offset-based** (APIs antiguas, SOAP)
Usa `$offset` y `$limit`

```json
{
  "pagination": {
    "enabled": true,
    "offset_param": "$offset",
    "limit_param": "$limit",
    "page_size": 50000
  }
}
```

### Estructura de Almacenamiento

Cuando se habilita paginación, los datos se guardan así:

```
raw-data/api/api_regalias/2025-11-24_183107/
├── page_0001.json  (10K registros)
├── page_0002.json  (10K registros)
├── page_0003.json  (10K registros)
└── ...
```

### Ejemplo Completo: Socrata

```json
{
  "id": "api_regalias",
  "name": "Consolidación de regalias por campo",
  "type": "api",
  "active": true,
  "schedule": { "cron": "0 * * * *", "note": "Every hour" },
  "config": {
    "base_url": "https://www.datos.gov.co/api/v3/views/j7js-yk74/query.json",
    "check_endpoint": "https://www.datos.gov.co/api/views/j7js-yk74.json",
    "check_field": "rowsUpdatedAt",
    "params": { "app_token": "$DATOS_GOV_TOKEN" },
    "headers": { "Accept": "application/json" },
    "timeout": 120,
    "pagination": {
      "enabled": true,
      "page_param": "pageNumber",
      "size_param": "pageSize",
      "page_size": 10000
    }
  },
  "storage": { "bucket": "raw-data" }
}
```

### Monitoreo de Paginación

Los logs mostrarán el progreso:

```
[api_loader] Descargando página 1 (pageNumber=1, pageSize=10000)
[api_loader] Página 1 guardada: api/api_regalias/2025-11-24_183107/page_0001.json
[api_loader] Descargando página 2 (pageNumber=2, pageSize=10000)
[api_loader] Página 2 guardada: api/api_regalias/2025-11-24_183107/page_0002.json
...
[api_loader] Última página detectada (solo 5432 filas < 10000)
[api_loader] Paginación completada: 15 páginas, 145432 filas totales
```

## Configuración Avanzada

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `timeout` | Tiempo máximo de respuesta en segundos | `60` |
| `max_retries` | Número de reintentos ante fallos | `3` |

**Ejemplo:**
```json
{
  "config": {
    "base_url": "https://api.ejemplo.com/data",
    "timeout": 30,
    "max_retries": 5,
    "auth_type": "bearer",
    "auth_key_env": "API_TOKEN"
  }
}
```
