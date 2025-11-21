/Datos2025/
│
├── data/                        ← ETL
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── scheduler/
│   │   ├── cron_jobs/           ← Configuración de cron
│   │   └── runner.py           ← Ejecuta workflows desde cron
│   │
│   ├── workflows/
│   │   ├── check_updates/
│   │   │   └── run.py           ← Detecta cambios
│   │   ├── full_etl/
│   │   │   └── run.py           ← Ejecuta descargas según fuente
│   │   └── sources_config.json  ← Fuentes + metadatos
│   │
│   ├── extraction/
│   │   ├── scrapers/            ← Playwright y scraping
│   │   ├── api_clients/         ← Cliente requests/API
│   │   └── common/              ← Utils comunes (fechas, hash, etc.)
│   │
│   ├── logging/
│   │   ├── logs/                ← Archivos persistentes
│   │   └── logger.py            ← Config de logs
│   │
│   └── services/
│       └── backend_client.py    ← Comunicación con API del backend
│
└── docker-compose.yml           ← Orquestación local

# Definir estructura final del Dockerfile
# Definir estructura interna del cron y runner
- config JSON externo con refresco dinámico

- sin credenciales en el JSON

- posible uso de Supabase e incluso webhooks

- enfoque solo en extracción RAW por ahora
# Definir formato de sources_config.json
# Definir flujo interno de check-updates