from abc import ABC, abstractmethod
from typing import Dict, Any
from logs_config.logger import app_logger as logger

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, source_config: Dict[str, Any]):
        """
        Ejecuta la lógica de extracción para la fuente dada.
        Debe descargar los datos y guardarlos en la ruta configurada (RAW).
        """
        pass
