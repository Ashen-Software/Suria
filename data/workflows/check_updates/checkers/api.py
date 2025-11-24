import requests
from typing import Dict, Any
from .base import BaseChecker
from common.env_resolver import resolve_dict_env_vars
from common.hash_utils import calculate_hash_sha256
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
            # Resolver variables de entorno en params y headers
            params = resolve_dict_env_vars(config.get("params", {}))
            headers = resolve_dict_env_vars(config.get("headers", {}))
            
            # Verificar si existe endpoint de chequeo (metadata)
            check_endpoint = config.get("check_endpoint")
            check_field = config.get("check_field")
            
            if check_endpoint and check_field:
                # Consulta metadata (mucho más ligero que descargar todo)
                logger.info(f"[ApiChecker] Consultando metadata de {src_id} en {check_endpoint}")
                response = requests.get(check_endpoint, timeout=10)
                response.raise_for_status()
                
                metadata = response.json()
                value_to_hash = str(metadata.get(check_field, ""))
                logger.info(f"[ApiChecker] Campo '{check_field}' obtenido: {value_to_hash}")
            else:
                # Fallback: consulta datos completos
                logger.info(f"[ApiChecker] Consultando datos completos de {url} para {src_id}")
                response = requests.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    timeout=60
                )
                response.raise_for_status()
                value_to_hash = response.content
            
            # Calcular hash SHA256
            current_hash = calculate_hash_sha256(value_to_hash)
            
            # Obtener estado previo
            last_state = self.client.get_source_state(src_id)
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
                    notes=f"Cambio detectado por {check_field if check_endpoint else 'hash SHA256'}"
                )
                return True
            
            logger.info(f"[ApiChecker] {src_id} sin cambios")
            
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
