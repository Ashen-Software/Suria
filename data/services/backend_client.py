from datetime import datetime
from typing import Dict, Optional, Any
from supabase import create_client, Client
from logs_config.logger import app_logger as logger
import settings

class BackendClient:
    def __init__(self):
        self.url: str = settings.SUPABASE_URL or ""
        self.key: str = settings.SUPABASE_KEY or ""
        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
            except Exception as e:
                logger.error(f"Error inicializando Supabase client: {e}")
        else:
            logger.warning("Credenciales de Supabase no encontradas en settings. BackendClient funcionando en modo limitado/local.")

    def get_source_state(self, source_id: str) -> Dict[str, Any]:
        """
        Obtiene el último estado registrado en el historial para una fuente.
        Consulta la tabla source_check_history ordenando por fecha descendente.
        """
        if not self.client:
            return {}
        
        try:
            # Obtenemos solo el registro más reciente
            response = self.client.table("source_check_history")\
                .select("*")\
                .eq("source_id", source_id)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception as e:
            logger.error(f"Error obteniendo historial para {source_id}: {e}")
        
        return {}

    def update_source_state(self, source_id: str, status: str, checksum: str = None, url: str = None, method: str = None, notes: str = None):
        """
        Inserta un nuevo registro en el historial de ejecuciones (source_check_history).
        """
        if not self.client:
            logger.info(f"[MOCK] Insertando historial {source_id}: status={status}")
            return

        # Construimos el metadata JSONB para no llenar la tabla de columnas dispersas
        metadata = {}
        if url: metadata["url"] = url
        if method: metadata["method"] = method
        if notes: metadata["notes"] = notes

        data = {
            "source_id": source_id,
            "status": status,
            "metadata": metadata
        }

        if checksum:
            data["checksum"] = checksum
        
        try:
            # Insertamos un nuevo registro historico
            self.client.table("source_check_history").insert(data).execute()
            
        except Exception as e:
            logger.error(f"Error insertando historial para {source_id}: {e}")
