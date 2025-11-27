"""
Módulo para descarga de archivos Excel con progreso.
"""
from typing import Dict, Any, Optional, Tuple
from io import BytesIO
from pathlib import Path

import requests
from tqdm import tqdm

from logs_config.logger import app_logger as logger
from extraction.scrapers.declaracion.file_manager import save_excel_to_raw, get_excel_filename_from_url


def download_excel_file(excel_url: str, excel_title: str, declaration: Optional[Dict[str, Any]] = None, save_to_disk: bool = True) -> Tuple[Optional[BytesIO], Optional[Path]]:
    """
    Descarga un archivo Excel desde una URL con barra de progreso y opcionalmente lo guarda en disco.
    
    Args:
        excel_url: URL del archivo Excel
        excel_title: Título del archivo para mostrar en la barra de progreso
        declaration: Diccionario con información de la declaración (opcional)
        save_to_disk: Si True, guarda el archivo en la carpeta raw
        
    Returns:
        Tupla (BytesIO con el contenido, Path del archivo guardado o None)
    """
    if not excel_url:
        logger.warning("[file_downloader] No hay URL de Excel")
        return None, None
    
    try:
        logger.info(f"[file_downloader] Descargando Excel: {excel_url}")
        
        response = requests.get(excel_url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        excel_bytes = BytesIO()
        downloaded = 0
        
        with tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            desc=f"Descargando {excel_title}"
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    excel_bytes.write(chunk)
                    downloaded += len(chunk)
                    pbar.update(len(chunk))
        
        excel_bytes.seek(0)
        file_size_mb = downloaded / (1024 * 1024)
        logger.info(f"[file_downloader] Excel descargado: {file_size_mb:.2f} MB")
        
        saved_path = None
        if save_to_disk:
            excel_bytes.seek(0)
            excel_content = excel_bytes.read()
            filename = get_excel_filename_from_url(excel_url)
            saved_path = save_excel_to_raw(excel_content, filename, declaration)
            excel_bytes.seek(0)
        
        return excel_bytes, saved_path
        
    except Exception as e:
        logger.error(f"[file_downloader] Error descargando Excel {excel_url}: {e}")
        return None, None

