"""
Utilidades para el scraper de declaraciones de gas natural.
"""
from typing import Dict


def month_to_number(month_name: str) -> str:
    """
    Convierte nombre de mes en español a número con formato MM.
    
    Args:
        month_name: Nombre del mes en español
        
    Returns:
        Número del mes como string con formato MM (01-12)
    """
    months: Dict[str, str] = {
        "enero": "01",
        "febrero": "02",
        "marzo": "03",
        "abril": "04",
        "mayo": "05",
        "junio": "06",
        "julio": "07",
        "agosto": "08",
        "septiembre": "09",
        "octubre": "10",
        "noviembre": "11",
        "diciembre": "12"
    }
    return months.get(month_name.lower(), "01")


def get_spanish_months_map() -> Dict[str, str]:
    """
    Retorna un diccionario con abreviaciones de meses en español.
    
    Returns:
        Diccionario con claves y valores iguales a las abreviaciones
    """
    return {
        "ene": "ene",
        "feb": "feb",
        "mar": "mar",
        "abr": "abr",
        "may": "may",
        "jun": "jun",
        "jul": "jul",
        "ago": "ago",
        "sep": "sep",
        "oct": "oct",
        "nov": "nov",
        "dic": "dic"
    }

