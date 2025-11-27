"""
Ejemplo de inserción de datos de declaraciones en Supabase.

Este script muestra cómo insertar los datos del JSON extraído
en las tablas de la base de datos Supabase.
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from supabase import create_client, Client
from logs_config.logger import app_logger as logger


def parse_datetime(datetime_str: str) -> datetime:
    """Parsea una fecha ISO a datetime."""
    try:
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except Exception as e:
        logger.warning(f"Error parseando fecha {datetime_str}: {e}")
        return datetime.now()


def insert_extraction_to_db(
    supabase: Client,
    extraction_data: Dict[str, Any]
) -> Optional[str]:
    """
    Inserta una extracción completa en la base de datos.
    
    Args:
        supabase: Cliente de Supabase
        extraction_data: Datos del JSON de extracción
        
    Returns:
        ID de la extracción insertada o None si hay error
    """
    try:
        # 1. Insertar extraction
        extraction_record = {
            "extraction_date": parse_datetime(extraction_data["extraction_date"]),
            "source_url": extraction_data["source_url"],
            "total_declarations": extraction_data.get("total_declarations", 0),
            "total_plantillas": extraction_data.get("total_plantillas", 0)
        }
        
        result = supabase.table("extractions").insert(extraction_record).execute()
        extraction_id = result.data[0]["id"]
        logger.info(f"[db_insert] Extracción insertada: {extraction_id}")
        
        # 2. Insertar declarations
        declarations = extraction_data.get("declarations", [])
        for declaration_data in declarations:
            declaration_record = {
                "extraction_id": extraction_id,
                "declaration_title": declaration_data["declaration_title"],
                "total_resolutions": declaration_data.get("total_resolutions", 0)
            }
            
            result = supabase.table("declarations").insert(declaration_record).execute()
            declaration_id = result.data[0]["id"]
            
            # 3. Insertar resolutions
            resolutions = declaration_data.get("resolutions", [])
            for resolution_data in resolutions:
                resolution_record = {
                    "declaration_id": declaration_id,
                    "number": resolution_data.get("number"),
                    "date": resolution_data.get("date"),  # Ya viene como YYYY-MM-DD
                    "url": resolution_data["url"],
                    "title": resolution_data["title"],
                    "extracted_data": resolution_data.get("extracted_data")  # JSONB
                }
                
                result = supabase.table("resolutions").insert(resolution_record).execute()
                resolution_id = result.data[0]["id"]
                
                # 4. Insertar soporte_magnetico
                soportes = resolution_data.get("soporte_magnetico")
                if soportes:
                    if isinstance(soportes, list):
                        for soporte_data in soportes:
                            soporte_record = {
                                "resolution_id": resolution_id,
                                "title": soporte_data["title"],
                                "url": soporte_data["url"],
                                "local_path": soporte_data.get("local_path"),
                                "file_size_bytes": soporte_data.get("file_size_bytes"),
                                "file_size_mb": soporte_data.get("file_size_mb")
                            }
                            supabase.table("soporte_magnetico").insert(soporte_record).execute()
                    else:
                        # Si es un solo objeto (no lista)
                        soporte_record = {
                            "resolution_id": resolution_id,
                            "title": soportes["title"],
                            "url": soportes["url"],
                            "local_path": soportes.get("local_path"),
                            "file_size_bytes": soportes.get("file_size_bytes"),
                            "file_size_mb": soportes.get("file_size_mb")
                        }
                        supabase.table("soporte_magnetico").insert(soporte_record).execute()
            
            # 5. Insertar cronograma (si existe)
            cronograma = declaration_data.get("cronograma")
            if cronograma:
                cronograma_record = {
                    "declaration_id": declaration_id,
                    "title": cronograma["title"],
                    "url": cronograma["url"]
                }
                supabase.table("cronogramas").insert(cronograma_record).execute()
            
            # 6. Insertar anexos (si existen)
            anexos = declaration_data.get("anexos", [])
            if anexos:
                for anexo_data in anexos:
                    anexo_record = {
                        "declaration_id": declaration_id,
                        "title": anexo_data["title"],
                        "url": anexo_data["url"]
                    }
                    supabase.table("anexos").insert(anexo_record).execute()
            
            # 7. Insertar acceso_sistema (si existe)
            acceso_sistema = declaration_data.get("acceso_sistema")
            if acceso_sistema:
                acceso_record = {
                    "declaration_id": declaration_id,
                    "title": acceso_sistema["title"],
                    "url": acceso_sistema["url"]
                }
                supabase.table("acceso_sistema").insert(acceso_record).execute()
        
        # 8. Insertar plantillas
        plantillas_grupos = extraction_data.get("plantillas", [])
        for plantilla_grupo in plantillas_grupos:
            plantilla_declaracion_record = {
                "extraction_id": extraction_id,
                "declaration_title": plantilla_grupo["declaration_title"]
            }
            
            result = supabase.table("plantillas_declaracion").insert(plantilla_declaracion_record).execute()
            plantilla_declaracion_id = result.data[0]["id"]
            
            # Insertar plantillas individuales
            plantillas = plantilla_grupo.get("plantillas", [])
            for plantilla_data in plantillas:
                plantilla_record = {
                    "plantilla_declaracion_id": plantilla_declaracion_id,
                    "type": plantilla_data["type"],
                    "title": plantilla_data["title"],
                    "url": plantilla_data["url"]
                }
                supabase.table("plantillas").insert(plantilla_record).execute()
        
        logger.info(f"[db_insert] Extracción {extraction_id} insertada exitosamente")
        return extraction_id
        
    except Exception as e:
        logger.error(f"[db_insert] Error insertando extracción: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_json_and_insert(json_path: str, supabase_url: str, supabase_key: str):
    """
    Carga un JSON y lo inserta en Supabase.
    
    Args:
        json_path: Ruta al archivo JSON
        supabase_url: URL de tu proyecto Supabase
        supabase_key: API key de Supabase (service_role key)
    """
    # Inicializar cliente de Supabase
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Cargar JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        extraction_data = json.load(f)
    
    # Insertar datos
    extraction_id = insert_extraction_to_db(supabase, extraction_data)
    
    if extraction_id:
        logger.info(f"[db_insert] Proceso completado. Extraction ID: {extraction_id}")
    else:
        logger.error("[db_insert] Error en el proceso de inserción")


if __name__ == "__main__":
    # Configuración - Ajustar según tu proyecto Supabase
    SUPABASE_URL = "https://tu-proyecto.supabase.co"
    SUPABASE_KEY = "tu-service-role-key-aqui"
    JSON_PATH = "data/extraction/scrapers/declaracion/processed/declaracion_20251126_164206.json"
    
    load_json_and_insert(JSON_PATH, SUPABASE_URL, SUPABASE_KEY)

