"""
Debug script: Inspecciona estructura JSON de archivos RAW descargados.

Útil para verificar qué estructura tiene el JSON respecto a data_path configurado.

Uso:
  python -m workflows.tests.debug_json_structure
"""
import json
import sys
from services.backend_client import BackendClient
from logs_config.logger import app_logger as logger


def inspect_json_structure(source_id: str = "api_regalias"):
    """
    Descarga PRIMER archivo RAW y muestra su estructura.
    
    Esto ayuda a identificar si data_path = "data" es correcto o necesita ajuste.
    """
    logger.info("="*70)
    logger.info("[DEBUG] Inspeccionando estructura JSON de archivos RAW")
    logger.info("="*70)
    
    try:
        client = BackendClient()
        bucket_name = "raw-data"
        prefix = f"api/{source_id}/"
        
        # Listar archivos
        files = client.list_files(bucket_name, prefix)
        if not files:
            logger.error(f"No hay archivos en {bucket_name}/{prefix}")
            return False
        
        logger.info(f"Total archivos encontrados: {len(files)}")
        
        # Descargar PRIMER archivo
        first_file = sorted(files)[0]
        logger.info(f"\nDescargando primer archivo: {first_file}")
        
        content_bytes = client.download_file(bucket_name, first_file)
        if not content_bytes:
            logger.error("No se pudo descargar el archivo")
            return False
        
        # Convertir a string
        if isinstance(content_bytes, bytes):
            content_str = content_bytes.decode('utf-8')
        else:
            content_str = str(content_bytes)
        
        # Parsear JSON
        try:
            data = json.loads(content_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON inválido: {e}")
            return False
        
        logger.info(f"\n[✓] Archivo descargado y parseado")
        logger.info(f"    - Tamaño: {len(content_str)} bytes")
        logger.info(f"    - Tipo de dato raíz: {type(data).__name__}")
        
        # Si es dict, mostrar keys principales
        if isinstance(data, dict):
            logger.info(f"\n[KEYS PRINCIPALES del JSON:]")
            for key in sorted(data.keys()):
                value = data[key]
                value_type = type(value).__name__
                
                # Si es lista, mostrar largo
                if isinstance(value, list):
                    logger.info(f"    - '{key}': {value_type} ({len(value)} items)")
                    if value:
                        logger.info(f"        → Primer item: {type(value[0]).__name__}")
                # Si es dict, mostrar keys
                elif isinstance(value, dict):
                    logger.info(f"    - '{key}': {value_type} (keys: {list(value.keys())[:5]}...)")
                # Si es valor simple
                else:
                    sample = str(value)[:50]
                    logger.info(f"    - '{key}': {value_type} → {sample}")
        
        # Si es lista directamente
        elif isinstance(data, list):
            logger.info(f"\n[ESTRUCTURA: Lista directa con {len(data)} items]")
            if data:
                logger.info(f"    - Tipo de item: {type(data[0]).__name__}")
                if isinstance(data[0], dict):
                    logger.info(f"    - Keys de primer item: {list(data[0].keys())}")
        
        # Mostrar muestra del primer registro
        logger.info(f"\n[MUESTRA del primer registro:]")
        if isinstance(data, dict):
            if "data" in data and data["data"]:
                first_record = data["data"][0] if isinstance(data["data"], list) else data["data"]
                logger.info(json.dumps(first_record, ensure_ascii=False, indent=2)[:500])
        elif isinstance(data, list) and data:
            first_record = data[0]
            logger.info(json.dumps(first_record, ensure_ascii=False, indent=2)[:500])
        
        logger.info(f"\n[RECOMENDACIÓN]")
        logger.info(f"Si los registros están bajo 'data', usar: data_path = 'data'")
        logger.info(f"Si los registros están en raíz (lista directa), usar: data_path = None")
        logger.info(f"Si los registros están bajo otra clave, usar: data_path = 'nombre_clave'")
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = inspect_json_structure()
    sys.exit(0 if success else 1)
