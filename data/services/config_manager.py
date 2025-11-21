import os
import json
from pathlib import Path
from typing import Dict, Any

from supabase import create_client
from loguru import logger

CACHE_DIR = Path(".cache")
CACHE_FILE = CACHE_DIR / "sources_config.json"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
CONFIG_BUCKET = os.getenv("CONFIG_BUCKET", "etl-configs")
CONFIG_OBJECT_NAME = os.getenv("CONFIG_OBJECT_NAME", "sources_config.json")


class ConfigManager:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Supabase ENV variables missing")

        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Ensure cache dir exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def download_remote_config(self) -> Dict[str, Any]:
        """
        Descarga el config desde Storage y lo devuelve como dict.
        """
        logger.info("Descargando configuración remota desde Supabase...")

        res = self.client.storage.from_(CONFIG_BUCKET).download(CONFIG_OBJECT_NAME)
        config_json = res.decode("utf-8")

        return json.loads(config_json)

    def load_local_config(self) -> Dict[str, Any] | None:
        """
        Retorna configuración local si existe.
        """
        if CACHE_FILE.exists():
            logger.info("Cargando configuración local desde cache…")
            return json.loads(CACHE_FILE.read_text())
        return None

    def save_local_config(self, config: Dict[str, Any]):
        """
        Actualiza archivo local con la última versión.
        """
        logger.info("Guardando nueva versión local del config…")
        CACHE_FILE.write_text(json.dumps(config, indent=2))

    def get_config(self) -> Dict[str, Any]:
        """
        Devuelve siempre el config actualizado.
        """
        local_config = self.load_local_config()
        remote_config = self.download_remote_config()

        if local_config != remote_config:
            logger.warning("Detectado cambio en configuración remota.")
            self.save_local_config(remote_config)
        else:
            logger.info("Config local ya está actualizado.")

        return remote_config


# EJEMPLO DE USO
if __name__ == "__main__":
    from services.config_manager import ConfigManager

    config = ConfigManager().get_config()
    sources = config["sources"]

    for source in sources:
        print("Procesando:", source["name"])