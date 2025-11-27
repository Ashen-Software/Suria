"""
Módulo para manejo de archivos locales (raw y processed).
"""
from pathlib import Path
from typing import Optional
from datetime import datetime
import json
from urllib.parse import urlparse

from logs_config.logger import app_logger as logger


BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"


def ensure_directories():
    """
    Asegura que los directorios raw y processed existan.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def save_excel_to_raw(excel_bytes: bytes, filename: Optional[str] = None, declaration: Optional[dict] = None) -> Path:
    """
    Guarda un archivo Excel en la carpeta raw.
    
    Args:
        excel_bytes: Contenido del archivo Excel en bytes
        filename: Nombre del archivo (opcional, se genera si no se proporciona)
        declaration: Diccionario con información de la declaración (opcional)
        
    Returns:
        Path del archivo guardado
    """
    ensure_directories()
    
    if not filename:
        if declaration:
            excel_title = declaration.get("excel_title", "")
            if excel_title:
                filename = _sanitize_filename(excel_title)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"declaracion_{timestamp}.xlsm"
        
        if not filename.endswith(('.xls', '.xlsx', '.xlsm')):
            filename += ".xlsm"
    
    file_path = RAW_DIR / filename
    
    with open(file_path, 'wb') as f:
        f.write(excel_bytes)
    
    logger.info(f"[file_manager] Excel guardado en: {file_path}")
    
    return file_path


def save_json_to_processed(data: dict, filename: Optional[str] = None) -> Path:
    """
    Guarda un JSON en la carpeta processed.
    
    Args:
        data: Diccionario con datos a guardar
        filename: Nombre del archivo (opcional, se genera si no se proporciona)
        
    Returns:
        Path del archivo guardado
    """
    ensure_directories()
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"declaracion_{timestamp}.json"
    
    if not filename.endswith('.json'):
        filename += ".json"
    
    file_path = PROCESSED_DIR / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"[file_manager] JSON guardado en: {file_path}")
    
    return file_path


def _sanitize_filename(filename: str) -> str:
    """
    Sanitiza un nombre de archivo removiendo caracteres inválidos.
    
    Args:
        filename: Nombre de archivo original
        
    Returns:
        Nombre de archivo sanitizado
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    filename = filename.strip()
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"declaracion_{timestamp}"
    
    return filename


def get_excel_filename_from_url(url: str) -> str:
    """
    Extrae el nombre de archivo desde una URL.
    
    Args:
        url: URL del archivo
        
    Returns:
        Nombre del archivo extraído
    """
    parsed_url = urlparse(url)
    filename = Path(parsed_url.path).name
    
    if not filename or filename == '/':
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"declaracion_{timestamp}.xlsm"
    
    return _sanitize_filename(filename)

