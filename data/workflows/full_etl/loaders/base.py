"""
Clase base abstracta para loaders.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseLoader(ABC):
    """
    Clase base para loaders de datos a PostgreSQL.
    
    Define el contrato mínimo que deben implementar los loaders.
    """
    
    @abstractmethod
    def load(self, records: List[Dict[str, Any]], source_id: str) -> Dict[str, Any]:
        """
        Carga registros transformados a la base de datos.
        
        Args:
            records: Lista de registros transformados (salida del transformer)
            source_id: ID de la fuente de datos
            
        Returns:
            Dict con estadísticas:
            {
                "status": "success" | "partial" | "error",
                "inserted": int,
                "updated": int,
                "errors": int,
                "error_details": List[Dict]
            }
        """
        pass
