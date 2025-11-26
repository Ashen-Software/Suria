import math
from typing import Any


def sanitize_value(value: Any) -> Any:
    """
    Sanitiza un valor para JSON/PostgreSQL.
    
    - Convierte NaN/Inf a None
    - Mantiene otros valores intactos
    """
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value