import os
import json
from pathlib import Path
from typing import Dict, Any

from supabase import create_client
from logs_config.logger import app_logger as logger
import settings

CACHE_DIR = Path(".cache")
CACHE_FILE = CACHE_DIR / "sources_config.json"

# Usar variables desde settings
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY


class ConfigManager:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase ENV variables missing - ConfigManager solo funcionará con cache local")
            self.client = None
        else:
            self.client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Ensure cache dir exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def get_remote_sources_from_db(self) -> list[Dict[str, Any]]:
        """
        Obtiene las fuentes desde la tabla 'etl_sources' de Supabase.
        Convierte el formato plano de la DB al formato anidado que espera el scheduler.
        """
        if not self.client:
            return []

        try:
            # logger.info("Consultando tabla 'etl_sources' en Supabase...")
            response = self.client.table("etl_sources").select("*").execute()
            
            # Convertir filas de DB a estructura de objetos del Scheduler
            sources = []
            for row in response.data:
                source = {
                    "id": row["id"],
                    "name": row["name"],
                    "active": row["active"],
                    "type": row["type"],
                    "schedule": {
                        "cron": row["schedule_cron"]
                    },
                    "config": row["config"],
                    "storage": row["storage_config"],
                    "force_change": False # Default
                }
                sources.append(source)
            
            return sources
        except Exception as e:
            logger.error("db_fetch_error", error=str(e))
            return []

    def load_local_config(self) -> Dict[str, Any] | None:
        """
        Retorna configuracion local si existe.
        """
        if CACHE_FILE.exists():
            logger.info("Cargando configuracion local desde cache…")
            return json.loads(CACHE_FILE.read_text())
        return None

    def save_local_config(self, config: Dict[str, Any]):
        """
        Actualiza archivo local con la ultima version.
        """
        logger.info("Guardando nueva version local del config…")
        CACHE_FILE.write_text(json.dumps(config, indent=2))

    def get_config(self) -> Dict[str, Any]:
        """
        Devuelve siempre el config actualizado.
        Prioriza: DB Supabase > Cache Local.
        """
        # 1. Intentar obtener desde Base de Datos
        try:
            db_sources = self.get_remote_sources_from_db()
            if db_sources:
                logger.info("Usando configuracion desde Base de Datos Supabase")
                config = {"sources": db_sources}
                # Actualizar cache local con la version de DB
                self.save_local_config(config)
                return config
        except Exception as e:
            logger.warning(f"Error consultando DB, intentando cache local: {e}")
        
        # 2. Fallback: usar cache local
        local_config = self.load_local_config()
        if local_config:
            logger.info("Usando configuracion desde cache local")
            return local_config
        
        # 3. Sin config disponible
        raise RuntimeError("No hay config disponible (ni DB ni cache local)")


# EJEMPLO DE USO
if __name__ == "__main__":
    from services.config_manager import ConfigManager

    config = ConfigManager().get_config()
    sources = config["sources"]

    for source in sources:
        print("Procesando:", source["name"])