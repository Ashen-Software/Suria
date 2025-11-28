"""
Configuración para el normalizador de gas natural (`proyeccion`).

Archivos de Series Históricas y de Proyección de Demanda de Gas Natural.
"""
from __future__ import annotations

from pathlib import Path

# Directorio base de este módulo (carpeta `proyeccion/`)
BASE_DIR: Path = Path(__file__).resolve().parent

# Directorio donde se almacenan los archivos Excel fuente
FILES_DIR: Path = BASE_DIR / "files"

# Rutas de archivos de Series Históricas de Gas Natural
# Patrón: "Series Históricas y de Proyección de Demanda de Gas Natural [YYYY] - [CATEGORIA].xlsx"
GAS_NATURAL_EXCEL_FILES = [
    # 2024
    FILES_DIR / "2024" / "Series Históricas y de Proyección de Demanda de Gas Natural 2024 - Compresores.xlsx",
    FILES_DIR / "2024" / "Series Históricas y de Proyección de Demanda de Gas Natural 2024 - Industrial.xlsx",
    FILES_DIR / "2024" / "Series Históricas y de Proyección de Demanda de Gas Natural 2024 - Petrolero.xlsx",
    FILES_DIR / "2024" / "Series Históricas y de Proyección de Demanda de Gas Natural 2024 - Petroquímico.xlsx",
    FILES_DIR / "2024" / "Series Históricas y de Proyección de Demanda de Gas Natural 2024 - Residencial.xlsx",
    FILES_DIR / "2024" / "Series Históricas y de Proyección de Demanda de Gas Natural 2024 - Terciario.xlsx",
    FILES_DIR / "2024" / "Series Históricas y de Proyección de Demanda de Gas Natural 2024 - TermoEléctrico.xlsx",
    FILES_DIR / "2024" / "Series Históricas y de Proyección de Demanda de Gas Natural Comprimido (GNC) – Transporte.xlsx",
    FILES_DIR / "2024" / "Series Históricas y de Proyección de Demanda de Gas Natural Licuado (GNL) – Transporte.xlsx",
    FILES_DIR / "2024" / "Series Históricas y de Proyección de Demanda de Gas Natural Agregada.xlsx",
    # 2023
    FILES_DIR / "2023" / "Series Históricas y de Proyección de Demanda de Gas Natural - Compresores.xlsx",
    FILES_DIR / "2023" / "Series Históricas y de Proyección de Demanda de Gas Natural - Industrial.xlsx",
    FILES_DIR / "2023" / "Series Históricas y de Proyección de Demanda de Gas Natural - Petrolero.xlsx",
    FILES_DIR / "2023" / "Series Históricas y de Proyección de Demanda de Gas Natural - Petroquímico.xlsx",
    FILES_DIR / "2023" / "Series Históricas y de Proyección de Demanda de Gas Natural - Residencial.xlsx",
    FILES_DIR / "2023" / "Series Históricas y de Proyección de Demanda de Gas Natural - Terciario.xlsx",
    FILES_DIR / "2023" / "Series Históricas y de Proyección de Demanda de Gas Natural - TermoEléctrico.xlsx",
    FILES_DIR / "2023" / "Series Históricas y de Proyección de Demanda de Gas Natural Comprimido (GNC) - Transporte.xlsx",
    FILES_DIR / "2023" / "Series Históricas y de Proyección de Demanda de Gas Natural Licuado (GNL) - Transporte.xlsx",
    FILES_DIR / "2023" / "Series Históricas y de Proyección de Demanda de Gas Natural - Agregado.xlsx",
]

# Mapeo de categorías desde nombres de archivo
CATEGORIA_MAP = {
    "compresores": "COMPRESORES",
    "industrial": "INDUSTRIAL",
    "petrolero": "PETROLERO",
    "petroquímico": "PETROQUIMICO",
    "residencial": "RESIDENCIAL",
    "terciario": "TERCIARIO",
    "termoeléctrico": "TERMOELECTRICO",
    "comprimido": "GNC_TRANSPORTE",
    "licuado": "GNL_TRANSPORTE",
    "agregada": "AGREGADO",
    "agregado": "AGREGADO",
}

# Ruta base donde se guardan los CSV normalizados
PROCESSED_DIR: Path = BASE_DIR / "processed"

# Subdirectorio para gas natural
PROCESSED_GAS_DIR: Path = PROCESSED_DIR / "gas-natural"

