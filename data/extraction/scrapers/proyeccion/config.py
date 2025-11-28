"""
Configuración local para el scraper de proyección (`proyeccion`).

La idea es centralizar aquí las rutas quemadas que usa el normalizador
para evitar tener literales repartidos por el código.
"""
from __future__ import annotations

from pathlib import Path

# Directorio base de este módulo (carpeta `proyeccion/`)
BASE_DIR: Path = Path(__file__).resolve().parent

# Directorio donde se almacenan los archivos Excel fuente
FILES_DIR: Path = BASE_DIR / "files"

# Rutas quemadas de los anexos Excel que queremos normalizar
# (relativas al repositorio, partiendo desde esta carpeta).
# Nota: El normalizer solo procesará los archivos que existan.
HARDCODED_EXCEL_FILES = [
    FILES_DIR / "2025" / "Anexo_proyeccion_demanda_2025_2039_verJul2025.xlsx",
    FILES_DIR / "2024" / "Anexo_proyeccion_demanda_2024_2038_v2_Jul2024.xlsx",
    FILES_DIR / "2023" / "Anexo_proyeccion_demanda_EE_2023_2037.xlsx",
    FILES_DIR / "2022" / "Anexo_Proyeccion_Demanda_EE_GN_CL_2022-2036_VF_jun.xlsx",
    FILES_DIR / "2021" / "UPME_Tablas_Proyeccion_DE_Junio_2021.xlsx",
    FILES_DIR / "2020" / "UPME_Tablas_Proyeccion_DE_Junio_2020.xlsx",
]

# Ruta base donde se guardan los CSV normalizados
PROCESSED_DIR: Path = BASE_DIR / "processed"

# Subdirectorios por tipo de métrica
PROCESSED_ENERGIA_DIR: Path = PROCESSED_DIR / "energia-electrica"
PROCESSED_POTENCIA_DIR: Path = PROCESSED_DIR / "potencia-maxima"
PROCESSED_CAPACIDAD_DIR: Path = PROCESSED_DIR / "capacidad-instalada"



