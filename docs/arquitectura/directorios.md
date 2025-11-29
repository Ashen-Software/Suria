# Directorios

## Proceso ETL
```text

/Suria/
│
├── data/                        ← ETL
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── scheduler/
│   │   ├── runner.py           ← Ejecuta workflows desde cron
│   │   └── jobs.py
│   │
│   ├── workflows/
│   │   ├── check_updates/
│   │   │   └── run.py           ← Detecta cambios
│   │   ├── full_etl/
│   │   │   └── run.py           ← Ejecuta descargas según fuente
│   │   └── sources_config.json  ← Fuentes + metadatos
│   │
│   ├── extraction/
│   │   ├── scrapers/
│   │   │   ├── declaracion/     ← Scrapers MinMinas
│   │   │   └── proyeccion/      ← Scrapers UPME
│   │   │       ├── config.py
│   │   │       ├── normalizer.py
│   │   │       └── schema/      ← Esquemas SQL por métrica
│   │   ├── api_clients/         ← Cliente requests/API
│   │   └── common/              ← Utils comunes (fechas, hash, etc.)
│   │
│   ├── logs_config/
│   │   ├── logs/                ← Archivos persistentes
│   │   └── logger.py            ← Config de logs
│   │
│   └── services/
│       └── backend_client.py    ← Comunicación con API del backend

```
