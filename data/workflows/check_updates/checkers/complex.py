from typing import Dict, Any
from .base import BaseChecker
from extraction.scrapers.scraper_loader import run_scraper_loader
from logs_config.logger import app_logger as logger

class ComplexScraperChecker(BaseChecker):
    """
    Checker que delega la verificación a un scraper complejo (Playwright/Selenium)
    ubicado en el módulo extraction/scrapers.
    """
    def check(self, source_config: Dict[str, Any]) -> bool:
        src_id = source_config.get("id")
        logger.info(f"[ComplexScraperChecker] Delegando verificación de {src_id} al módulo de scrapers")
        
        try:
            # Aquí invocamos al scraper loader. 
            # Dependiendo de cómo esté implementado scraper_loader, podría retornar 
            # el estado actual o guardar el archivo.
            # Asumiremos que run_scraper_loader retorna un dict con metadatos o hash.
            
            # Nota: run_scraper_loader es un placeholder actualmente.
            # En una implementación real, le pasaríamos un flag 'check_only=True' 
            # para que solo verifique y no descargue todo si no es necesario.
            current_value = run_scraper_loader(source_config)
            
            # Hasheamos el resultado retornado por el script custom
            import hashlib
            current_hash = hashlib.md5(str(current_value).encode('utf-8')).hexdigest()
            
            last_state = self.client.get_source_state(src_id)
            last_hash = last_state.get("checksum")
            
            if current_hash != last_hash:
                logger.info(f"[ComplexScraperChecker] Cambio detectado en {src_id}. Hash anterior: {last_hash}, Nuevo: {current_hash}")
                self.client.update_source_state(
                    source_id=src_id,
                    status="changed",
                    checksum=current_hash,
                    method="complex_scraper",
                    notes="Cambio detectado por script custom"
                )
                return True
            
            logger.info(f"[ComplexScraperChecker] {src_id} sin cambios")
            self.client.update_source_state(
                source_id=src_id,
                status="no_change",
                checksum=current_hash,
                method="complex_scraper",
                notes="Verificación custom exitosa"
            )
            return False # Placeholder
            
        except Exception as e:
            error_msg = f"Error en ComplexScraperChecker para {src_id}: {e}"
            logger.error(error_msg)
            self.client.update_source_state(
                source_id=src_id,
                status="failed",
                method="complex_scraper",
                notes=error_msg
            )
            return False
