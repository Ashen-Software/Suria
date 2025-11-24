from abc import ABC, abstractmethod
from typing import Dict, Any
from logs_config.logger import app_logger as logger
from services.backend_client import BackendClient

class BaseChecker(ABC):
    def __init__(self, backend_client: BackendClient):
        self.client = backend_client

    @abstractmethod
    def check(self, source_config: Dict[str, Any]) -> bool:
        """
        Verifica si hay actualizaciones para la fuente dada.
        Retorna True si hay cambios, False en caso contrario.
        Si hay cambios, debe encargarse de actualizar el estado en el backend 
        (o delegarlo, dependiendo de la estrategia de consistencia).
        """
        pass
