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
            # Obtenemos solo el registro mas reciente
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

    def upload_file(self, bucket_name: str, file_path: str, file_content: bytes, content_type: str = "application/octet-stream"):
        """
        Sube un archivo a un bucket de Supabase Storage.
        :param bucket_name: Nombre del bucket (ej: 'raw-data')
        :param file_path: Ruta dentro del bucket (ej: 'fuente_1/2023/10/file.json')
        :param file_content: Contenido del archivo en bytes
        :param content_type: Tipo MIME del archivo
        """
        if not self.client:
            logger.info(f"[MOCK] Subiendo archivo a bucket '{bucket_name}': {file_path}")
            return

        try:
            # upsert='true' permite sobrescribir si ya existe
            self.client.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            logger.info(f"Archivo subido a Supabase Storage: {bucket_name}/{file_path}")
        except Exception as e:
            logger.error(f"Error subiendo archivo a Storage {bucket_name}/{file_path}: {e}")
            raise
