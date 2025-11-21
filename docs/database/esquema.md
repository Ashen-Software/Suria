# Esquema

## data_sources_status
| Campo               | Tipo                               | Descripción                                            |
| ------------------- | ---------------------------------- | ------------------------------------------------------ |
| `source_id`         | string                             | Identificador interno ("ministerio", "api_gas", etc.). |
| `source_url`        | string                             | URL base o endpoint.                                   |
| `update_method`     | enum(api, scraping, html, archivo) | Define cómo chequear cambios.                          |
| `last_known_update` | datetime                           | Última actualización detectada y procesada.            |
| `last_check`        | datetime                           | Última vez revisado.                                   |
| `checksum`          | string (opcional)                  | Huella del archivo, útil si no hay fecha disponible.   |
| `status`            | enum(no_change, changed, failed)   | Resultado del último chequeo.                          |
| `notes`             | text                               | Mensajes de error o logs.                              |
