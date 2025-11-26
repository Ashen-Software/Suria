import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env si existe (local)
# Ruta relativa a este archivo (data/settings.py -> data/.env)
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# General
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
SERVICE_NAME = os.getenv("SERVICE_NAME", "etl_service")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") # Usamos la Service Key


# Scheduler / Config
# CONFIG_POLL_INTERVAL = int(os.getenv("CONFIG_POLL_INTERVAL", "300"))
CONFIG_RELOAD_INTERVAL = int(os.getenv("CONFIG_RELOAD_INTERVAL", "120"))
USE_REMOTE_CONFIG = os.getenv("USE_REMOTE_CONFIG", "false").lower() == "true"

# Logs
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR_ENV = os.getenv("LOG_DIR") 
