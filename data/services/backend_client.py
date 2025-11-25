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

    def list_files(self, bucket_name: str, prefix: str = "") -> Optional[list]:
        """
        Lista archivos en un bucket de Supabase Storage con un prefijo opcional.
        
        :param bucket_name: Nombre del bucket (ej: 'raw-data')
        :param prefix: Prefijo para filtrar archivos (ej: 'api/api_regalias/')
        :return: Lista de rutas de archivos, o None si error
        
        Ejemplo:
            files = client.list_files("raw-data", "api/api_regalias/")
            # Retorna: ["api/api_regalias/2024-11-25_120000.json", ...]
        """
        if not self.client:
            logger.warning(f"[MOCK] Listando archivos en bucket '{bucket_name}' con prefijo '{prefix}'")
            return []

        try:
            response = self.client.storage.from_(bucket_name).list(path=prefix)
            
            if not response:
                logger.warning(f"No hay archivos en {bucket_name}/{prefix}")
                return None
            
            # response es una lista de dicts con 'name', 'id', 'updated_at', 'created_at', 'last_accessed_at', 'metadata'
            # Construir rutas completas
            files = []
            for item in response:
                if item.get("name"):
                    # Si el item tiene 'id' (es un archivo), agregarlo a la lista
                    # Si es un folder, recursivamente listar contenido
                    full_path = f"{prefix}{item['name']}" if prefix else item["name"]
                    
                    if item.get("id"):  # Es un archivo (tiene ID)
                        files.append(full_path)
                    else:  # Es una carpeta, listar recursivamente
                        sub_files = self.list_files(bucket_name, full_path + "/")
                        if sub_files:
                            files.extend(sub_files)
            
            logger.debug(f"Archivos listados en {bucket_name}/{prefix}: {len(files)} archivo(s)")
            return files if files else None
            
        except Exception as e:
            logger.error(f"Error listando archivos en {bucket_name}/{prefix}: {e}")
            return None

    def download_file(self, bucket_name: str, file_path: str) -> Optional[bytes]:
        """
        Descarga un archivo de un bucket de Supabase Storage.
        
        :param bucket_name: Nombre del bucket (ej: 'raw-data')
        :param file_path: Ruta dentro del bucket (ej: 'api/api_regalias/2024-11-25_120000.json')
        :return: Contenido del archivo en bytes, o None si error
        
        Ejemplo:
            content = client.download_file("raw-data", "api/api_regalias/2024-11-25_120000.json")
            data = json.loads(content.decode('utf-8'))
        """
        if not self.client:
            logger.info(f"[MOCK] Descargando archivo de bucket '{bucket_name}': {file_path}")
            return None

        try:
            response = self.client.storage.from_(bucket_name).download(file_path)
            
            if response:
                logger.debug(f"Archivo descargado de {bucket_name}/{file_path}")
                return response
            else:
                logger.warning(f"Archivo vacío o no encontrado: {bucket_name}/{file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error descargando archivo de {bucket_name}/{file_path}: {e}")
            return None
