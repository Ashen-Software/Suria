"""
Scraper para Declaraciones de Producción de Gas Natural del Ministerio de Minas y Energía.

Este scraper (EXTRACTION):
- Accede a la página de gas natural usando requests + BeautifulSoup
- Extrae declaraciones, resoluciones, cronogramas, anexos y plantillas
- Descarga archivos Excel (.xlsm/.xlsx) crudos al bucket
- NO parsea los Excel (eso se hace en TRANSFORMATION)
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from logs_config.logger import app_logger as logger
from common.hash_utils import calculate_hash_sha256

from extraction.scrapers.declaracion.web_scraper import extract_declaration_links
from extraction.scrapers.declaracion.file_downloader import download_excel_file


def check(source_config: Dict[str, Any]) -> str:
    """
    Detecta cambios en la página de declaraciones de gas natural.
    
    Args:
        source_config: Configuración de la fuente
        
    Returns:
        String hashable con el estado actual (lista de resoluciones y Excel)
    """
    config = source_config.get("config", {})
    url = config.get(
        "url",
        "https://www.minenergia.gov.co/es/misional/hidrocarburos/funcionamiento-del-sector/gas-natural/"
    )
    
    logger.info(f"[gas_natural_declaracion] Verificando cambios en {url}")
    
    try:
        declarations = extract_declaration_links(url)
        
        state_str = json.dumps(declarations, sort_keys=True)
        checksum = calculate_hash_sha256(state_str)
        
        logger.info(
            f"[gas_natural_declaracion] Estado actual: "
            f"{len(declarations)} declaraciones encontradas"
        )
        
        return checksum
        
    except Exception as e:
        logger.error(f"[gas_natural_declaracion] Error en check: {e}")
        raise


def extract(source_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae archivos Excel de declaraciones de gas natural.
    
    Args:
        source_config: Configuración de la fuente
        
    Returns:
        Dict con estructura:
        {
            "metadata": bytes (JSON con metadata),
            "excel_files": [
                {"filename": str, "content": bytes, "parsed_data": dict|None},
                ...
            ]
        }
        
        Esta estructura permite al extractor guardar:
        - metadata.json con enlaces y estructura
        - excel/*.xlsx archivos originales
        - parsed/*.json datos parseados de cada Excel
    """
    config = source_config.get("config", {})
    url = config.get(
        "url",
        "https://www.minenergia.gov.co/es/misional/hidrocarburos/funcionamiento-del-sector/gas-natural/"
    )
    
    logger.info(f"[gas_natural_declaracion] Iniciando extracción desde {url}")
    
    try:
        declarations = extract_declaration_links(url)
        
        logger.info(
            f"[gas_natural_declaracion] Encontradas {len(declarations)} declaraciones"
        )
        
        analyze_excel = config.get("analyze_excel", False)
        
        limit_files = config.get("limit_files")
        if limit_files and analyze_excel:
            declarations = declarations[:limit_files]
            logger.info(
                f"[gas_natural_declaracion] Limitando a {limit_files} "
                f"declaración(es) para procesamiento"
            )
        elif limit_files and not analyze_excel:
            logger.info(
                f"[gas_natural_declaracion] Ignorando limit_files cuando analyze_excel=False "
                f"(extrayendo todas las declaraciones)"
            )
        
        limit_resolutions = config.get("limit_resolutions")
        if limit_resolutions and analyze_excel:
            logger.info(
                f"[gas_natural_declaracion] Limitando a {limit_resolutions} "
                f"resolución(es) por declaración"
            )
        elif limit_resolutions and not analyze_excel:
            logger.info(
                f"[gas_natural_declaracion] Ignorando limit_resolutions cuando analyze_excel=False "
                f"(extrayendo todas las resoluciones)"
            )
        if analyze_excel:
            logger.info("[gas_natural_declaracion] Modo activado: Descarga y análisis de Excel")
        else:
            logger.info("[gas_natural_declaracion] Modo desactivado: Solo extracción de enlaces")
        
        processed_declarations = []
        processed_plantillas = []
        excel_files = []
        
        for idx, declaration in enumerate(declarations, 1):
            declaration_type = declaration.get("type")
            
            if declaration_type == "plantillas":
                plantilla_data = {
                    "type": "plantillas",
                    "declaration_title": declaration.get("declaration_title"),
                    "plantillas": declaration.get("plantillas", [])
                }
                if plantilla_data["plantillas"]:
                    processed_plantillas.append(plantilla_data)
                continue
            
            declaration_title = declaration.get("declaration_title", "Unknown")
            logger.info(
                f"[gas_natural_declaracion] Procesando declaración {idx}/{len(declarations)}: {declaration_title}"
            )
            
            processed_declaration = _process_declaration(
                declaration, 
                limit_resolutions if analyze_excel else None, 
                analyze_excel,
                excel_files
            )
            
            if processed_declaration:
                processed_declarations.append(processed_declaration)
        
        result = {
            "extraction_date": datetime.now().isoformat(),
            "source_url": url,
            "declarations": processed_declarations,
            "total_declarations": len(processed_declarations)
        }
        
        if processed_plantillas:
            result["plantillas"] = processed_plantillas
            result["total_plantillas"] = len(processed_plantillas)
        
        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        
        total_resolutions = sum(len(d.get("resolutions", [])) for d in processed_declarations)
        logger.info(
            f"[gas_natural_declaracion] Extracción completada: "
            f"{len(processed_declarations)} declaraciones, {total_resolutions} resoluciones, "
            f"{len(excel_files)} archivos Excel"
        )
        
        # # Guardar copia local solo si esta habilitado (debug/desarrollo)
        # save_local = config.get("save_local_copy", False)
        # if save_local:
        #     save_json_to_processed(result)
        #     logger.info("[gas_natural_declaracion] Copia local guardada (save_local_copy=True)")
        
        # Retornar estructura con metadata y archivos Excel
        return {
            "metadata": result_json.encode('utf-8'),
            "excel_files": excel_files
        }
        
    except Exception as e:
        logger.error(f"[gas_natural_declaracion] Error en extract: {e}")
        raise


def _process_declaration(
    declaration: Dict[str, Any], 
    limit_resolutions: Optional[int] = None, 
    analyze_excel: bool = False,
    excel_files: Optional[list] = None
) -> Optional[Dict[str, Any]]:
    """
    Procesa una declaración completa con todas sus resoluciones.
    
    Args:
        declaration: Diccionario con la declaración y sus resoluciones
        limit_resolutions: Límite opcional de resoluciones a procesar
        analyze_excel: Si es True, descarga y analiza el contenido del Excel
        excel_files: Lista donde acumular archivos Excel descargados (mutada in-place)
        
    Returns:
        Diccionario con la declaración procesada o None si hay error
    """
    if excel_files is None:
        excel_files = []
        
    declaration_title = declaration.get("declaration_title", "Unknown")
    resolutions = declaration.get("resolutions", [])
    cronograma = declaration.get("cronograma")
    anexos = declaration.get("anexos", [])
    acceso_sistema = declaration.get("acceso_sistema")
    
    if not resolutions:
        logger.warning(f"[gas_natural_declaracion] No hay resoluciones en la declaración: {declaration_title}")
        return None
    
    if limit_resolutions and resolutions:
        resolutions = resolutions[:limit_resolutions]
        logger.info(
            f"[gas_natural_declaracion] Limitando a {limit_resolutions} resoluciones "
            f"para {declaration_title}"
        )
    
    processed_resolutions = []
    
    for resolution in resolutions:
        soporte_magnetico = resolution.get("soporte_magnetico")
        
        if not soporte_magnetico or (isinstance(soporte_magnetico, list) and len(soporte_magnetico) == 0):
            logger.info(f"[gas_natural_declaracion] Resolución sin soporte magnético (solo link PDF): {resolution.get('title')}")
            processed_resolutions.append({
                **resolution,
                "soporte_magnetico": None,
                "extracted_data": None
            })
            continue
        
        soportes_list = soporte_magnetico if isinstance(soporte_magnetico, list) else [soporte_magnetico]
        
        processed_soportes = []
        excel_file_processed = False
        
        for soporte in soportes_list:
            soporte_url = soporte.get("url")
            soporte_title = soporte.get("title", "")
            soporte_url_lower = soporte_url.lower() if soporte_url else ""
            
            is_excel = (
                ".xls" in soporte_url_lower or 
                ".xlsx" in soporte_url_lower or 
                ".xlsm" in soporte_url_lower or
                "excel" in soporte_title.lower()
            )
            
            processed_soporte = {
                "title": soporte_title,
                "url": soporte_url,
                "local_path": None,
                "file_size_bytes": None,
                "file_size_mb": None
            }
            
            if analyze_excel and is_excel and not excel_file_processed:
                logger.info(f"[gas_natural_declaracion] Descargando Excel: {soporte_title}")
                
                excel_declaration = {
                    "period": declaration_title,
                    "resolution": resolution,
                    "excel_url": soporte_url,
                    "excel_title": soporte_title
                }
                
                # No guardar a disco local, solo descargar en memoria
                excel_bytes, _ = download_excel_file(
                    soporte_url, soporte_title, excel_declaration, save_to_disk=False
                )
                
                if excel_bytes:
                    file_size_bytes = excel_bytes.getbuffer().nbytes
                    file_size_mb = file_size_bytes / (1024 * 1024)
                    
                    # Generar nombre de archivo para el bucket
                    resolution_num = resolution.get("number", "unknown")
                    # Determinar extensión del archivo original
                    if ".xlsm" in soporte_url_lower:
                        ext = "xlsm"
                    elif ".xlsx" in soporte_url_lower:
                        ext = "xlsx"
                    else:
                        ext = "xls"
                    excel_filename = f"res_{resolution_num}.{ext}"
                    
                    processed_soporte["file_size_bytes"] = file_size_bytes
                    processed_soporte["file_size_mb"] = file_size_mb
                    processed_soporte["bucket_path"] = f"excel/{excel_filename}"
                    
                    # Solo guardar el Excel crudo, sin parsear
                    # El parseo se hará en el paso de TRANSFORMATION
                    excel_bytes.seek(0)
                    excel_files.append({
                        "filename": excel_filename,
                        "content": excel_bytes.read(),
                        "declaration_title": declaration_title,
                        "resolution_number": resolution_num
                    })
                    
                    logger.info(
                        f"[gas_natural_declaracion] Excel descargado: {excel_filename} "
                        f"({file_size_mb:.2f} MB)"
                    )
                    
                    excel_file_processed = True
                else:
                    logger.warning(f"[gas_natural_declaracion] No se pudo descargar el Excel: {soporte_title}")
            elif analyze_excel and is_excel:
                logger.info(f"[gas_natural_declaracion] Saltando descarga adicional de Excel (ya se procesó uno): {soporte_title}")
            
            processed_soportes.append(processed_soporte)
        
        processed_resolution = {
            "number": resolution.get("number"),
            "date": resolution.get("date"),
            "url": resolution.get("url"),
            "title": resolution.get("title"),
            "soporte_magnetico": processed_soportes if len(processed_soportes) > 0 else None
        }
        
        processed_resolutions.append(processed_resolution)
    
    result = {
        "declaration_title": declaration_title,
        "resolutions": processed_resolutions,
        "total_resolutions": len(processed_resolutions)
    }
    
    if cronograma:
        result["cronograma"] = cronograma
    if anexos:
        result["anexos"] = anexos
        result["total_anexos"] = len(anexos)
    if acceso_sistema:
        result["acceso_sistema"] = acceso_sistema
    
    return result
