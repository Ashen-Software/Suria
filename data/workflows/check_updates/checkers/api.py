from typing import Dict, Any
import requests
import hashlib
from .base import BaseChecker
from logs_config.logger import app_logger as logger

class ApiChecker(BaseChecker):
    def check(self, source_config: Dict[str, Any]) -> bool:
        config = source_config.get("config", {})
        url = config.get("base_url")
        src_id = source_config.get("id")
        
        if not url:
            logger.error(f"Configuración inválida para API: falta base_url en {src_id}")
            return False
            
        try:
            logger.info(f"[ApiChecker] Conectando a {url} para {src_id}")
            response = requests.get(
                url, 
                params=config.get("params"), 
                headers=config.get("headers"), 
                timeout=10
            )
            response.raise_for_status()
            
            # Calcular hash del contenido
            current_hash = hashlib.md5(response.content).hexdigest()
            
            # Obtener estado previo
            last_state = self.client.get_source_state(src_id)
            last_hash = last_state.get("checksum")
            
            if current_hash != last_hash:
                logger.info(f"[ApiChecker] Cambio detectado en {src_id}. Hash anterior: {last_hash}, Nuevo: {current_hash}")
                
                self.client.update_source_state(
                    source_id=src_id,
                    status="changed",
                    checksum=current_hash,
                    url=url,
                    method="api",
                    notes="Cambio detectado por hash MD5"
                )
                return True
            
            logger.info(f"[ApiChecker] {src_id} sin cambios (Hash: {current_hash})")
            
            # Actualizamos el "visto por ultima vez" aunque no haya cambios
            self.client.update_source_state(
                source_id=src_id,
                status="no_change",
                checksum=current_hash,
                url=url,
                method="api",
                notes="Verificación exitosa, sin cambios"
            )
            return False 
            
        except Exception as e:
            error_msg = f"Error verificando API {src_id}: {str(e)}"
            logger.error(error_msg)
            
            # Registramos el fallo en la base de datos
            self.client.update_source_state(
                source_id=src_id,
                status="failed",
                url=url,
                method="api",
                notes=error_msg
            )
            return False
