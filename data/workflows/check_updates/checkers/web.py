from typing import Dict, Any
import requests
import hashlib
from bs4 import BeautifulSoup
from .base import BaseChecker
from logs_config.logger import app_logger as logger

class WebScraperChecker(BaseChecker):
    def check(self, source_config: Dict[str, Any]) -> bool:
        config = source_config.get("config", {})
        url = config.get("url")
        src_id = source_config.get("id")

        if not url:
            logger.error(f"Configuración inválida para Scraper: falta url en {src_id}")
            return False
            
        try:
            logger.info(f"[WebScraperChecker] Conectando a {url} para {src_id}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Usamos BeautifulSoup para limpiar o extraer solo lo relevante antes de hashear
            # Esto evita falsos positivos por cambios en scripts o ads
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Si hay un selector específico en config, lo usamos
            selector = config.get("selector", "body")
            element = soup.select_one(selector)
            content_to_hash = str(element) if element else response.text
            
            current_hash = hashlib.md5(content_to_hash.encode('utf-8')).hexdigest()
            
            last_state = self.client.get_source_state(src_id)
            last_hash = last_state.get("checksum") # Actualizado de last_hash a checksum
            
            if current_hash != last_hash:
                logger.info(f"[WebScraperChecker] Cambio detectado en {src_id}. Hash anterior: {last_hash}, Nuevo: {current_hash}")
                self.client.update_source_state(
                    source_id=src_id,
                    status="changed",
                    checksum=current_hash,
                    url=url,
                    method="scraping",
                    notes="Cambio detectado en contenido HTML"
                )
                return True
            
            logger.info(f"[WebScraperChecker] {src_id} sin cambios")
            
            self.client.update_source_state(
                source_id=src_id,
                status="no_change",
                checksum=current_hash,
                url=url,
                method="scraping",
                notes="Verificación exitosa, sin cambios"
            )
            return False
            
        except Exception as e:
            error_msg = f"Error verificando Web {src_id}: {str(e)}"
            logger.error(error_msg)
            
            self.client.update_source_state(
                source_id=src_id,
                status="failed",
                url=url,
                method="scraping",
                notes=error_msg
            )
            return False
