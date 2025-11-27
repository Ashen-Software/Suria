"""
Módulo para scraping web de declaraciones de gas natural usando requests + BeautifulSoup.
"""
from typing import Dict, Any, List, Tuple, Optional
import re
import traceback
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from logs_config.logger import app_logger as logger
from extraction.scrapers.declaracion.utils import month_to_number


def extract_declaration_links(page) -> List[Dict[str, Any]]:
    """
    Extrae declaraciones con su estructura jerárquica completa usando requests + BeautifulSoup.
    
    Args:
        page: URL (str) de la página a scrapear
    
    Returns:
        Lista de declaraciones con estructura jerárquica
    """
    declarations = []
    
    try:
        if not isinstance(page, str):
            raise ValueError("El parámetro 'page' debe ser una URL (string)")
        
        url = page or "https://www.minenergia.gov.co/es/misional/hidrocarburos/funcionamiento-del-sector/gas-natural/"
        
        logger.info(f"[web_scraper] Descargando HTML de {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        logger.info("[web_scraper] Parseando HTML con BeautifulSoup...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        all_accordion_items = soup.find_all('div', class_='accordion-item')
        logger.info(f"[web_scraper] Encontrados {len(all_accordion_items)} acordeones en total")
        
        declarations_dict = {}
        
        for accordion_item in all_accordion_items:
            accordion_button = accordion_item.find('button', class_='accordion-button')
            if not accordion_button:
                continue
            
            accordion_title = accordion_button.get_text(strip=True)
            accordion_body = accordion_item.find('div', class_='accordion-body')
            
            if not accordion_body:
                continue
            
            if "Declaración de Producción de Gas Natural" in accordion_title:
                period_match = re.search(r'(\d{4})\s*-\s*(\d{4})', accordion_title)
                if period_match:
                    period_pattern = f"{period_match.group(1)} - {period_match.group(2)}"
                    declaration_title = f"Declaración de Producción de Gas Natural {period_pattern}"
                    
                    if declaration_title not in declarations_dict:
                        declarations_dict[declaration_title] = {
                            "declaration_title": declaration_title,
                            "resolutions": [],
                            "cronograma": None,
                            "anexos": [],
                            "acceso_sistema": None
                        }
                    
                    resolutions, cronograma, anexos, acceso_sistema = extract_resolutions_and_metadata_from_accordion(accordion_body, period_pattern, url)
                    declarations_dict[declaration_title]["resolutions"].extend(resolutions)
                    if cronograma:
                        declarations_dict[declaration_title]["cronograma"] = cronograma
                    if anexos:
                        declarations_dict[declaration_title]["anexos"].extend(anexos)
                    if acceso_sistema:
                        declarations_dict[declaration_title]["acceso_sistema"] = acceso_sistema
            
            elif "Plantillas de cargue Declaración" in accordion_title or "Plantillas de cargue" in accordion_title:
                plantilla_title = accordion_title
                plantilla_data = {
                    "type": "plantillas",
                    "declaration_title": plantilla_title,
                    "plantillas": []
                }
                plantillas = extract_plantillas_from_accordion(accordion_body, url)
                plantilla_data["plantillas"].extend(plantillas)
                if plantilla_data["plantillas"]:
                    declarations.append(plantilla_data)
        
        declarations.extend(declarations_dict.values())
        
        logger.info(f"[web_scraper] Extraídas {len(declarations)} declaraciones en total")
        
    except Exception as e:
        logger.error(f"[web_scraper] Error extrayendo enlaces: {e}")
        traceback.print_exc()
        raise
    
    return declarations


def extract_resolutions_and_metadata_from_accordion(
    accordion_body, 
    period_pattern: str, 
    base_url: str
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, str]], List[Dict[str, str]], Optional[Dict[str, str]]]:
    """
    Extrae resoluciones, cronograma, anexos y acceso al sistema desde un elemento accordion-body.
    
    Args:
        accordion_body: Elemento BeautifulSoup del accordion-body
        period_pattern: Patrón del período
        base_url: URL base
        
    Returns:
        Tupla con (resoluciones, cronograma, anexos, acceso_sistema)
    """
    resolutions = extract_resolutions_from_accordion(accordion_body, period_pattern, base_url)
    
    cronograma = None
    anexos = []
    acceso_sistema = None
    
    try:
        all_text = accordion_body.get_text()
        all_links = accordion_body.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            text_lower = text.lower()
            
            if not href or not text:
                continue
            
            full_url = urljoin(base_url, href)
            
            if "cronograma" in text_lower and "ver comunicado" in text_lower:
                cronograma = {
                    "title": text,
                    "url": full_url
                }
            elif "anexo" in text_lower and not any(skip in text_lower for skip in ["resolución", "resolucion", "soporte"]):
                anexos.append({
                    "title": text,
                    "url": full_url
                })
            elif ("sistema" in text_lower and "acceso" in text_lower) or "declaragas" in href.lower():
                acceso_sistema = {
                    "title": text,
                    "url": full_url
                }
        
        if not cronograma:
            cronograma_match = re.search(r'(Ver Comunicado Cronograma[^\.]*)', all_text, re.IGNORECASE)
            if cronograma_match:
                cronograma_text = cronograma_match.group(1).strip()
                for link in all_links:
                    if cronograma_text.lower() in link.get_text(strip=True).lower():
                        cronograma = {
                            "title": cronograma_text,
                            "url": urljoin(base_url, link.get('href', ''))
                        }
                        break
        
        if not acceso_sistema:
            for link in all_links:
                href_lower = link.get('href', '').lower()
                if 'declaragas' in href_lower:
                    acceso_sistema = {
                        "title": link.get_text(strip=True),
                        "url": urljoin(base_url, link.get('href', ''))
                    }
                    break
        
    except Exception as e:
        logger.error(f"[web_scraper] Error extrayendo metadata: {e}")
    
    return resolutions, cronograma, anexos, acceso_sistema


def extract_resolutions_from_accordion(accordion_body, period_pattern: str, base_url: str) -> List[Dict[str, Any]]:
    """
    Extrae resoluciones desde un elemento accordion-body.
    
    Args:
        accordion_body: Elemento BeautifulSoup del accordion-body
        period_pattern: Patrón del período
        base_url: URL base
        
    Returns:
        Lista de resoluciones
    """
    resolutions = []
    
    try:
        all_links = accordion_body.find_all('a', href=True)
        
        current_resolution = None
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if not href or not text:
                continue
            
            full_url = urljoin(base_url, href)
            text_lower = text.lower()
            
            is_soporte_magnetico = (
                ("soporte magnético" in text_lower or "soporte magnetico" in text_lower) or
                (".xls" in href.lower() or ".xlsx" in href.lower() or ".xlsm" in href.lower()) or
                ("(pdf)" in text_lower or "(excel)" in text_lower or "(xls)" in text_lower)
            )
            
            is_resolucion_principal = (
                ("resolución" in text_lower or "resolucion" in text_lower) and
                not is_soporte_magnetico and
                not ("soporte" in text_lower)
            )
            
            if is_resolucion_principal:
                if current_resolution:
                    if not current_resolution.get("soporte_magnetico") or len(current_resolution.get("soporte_magnetico", [])) == 0:
                        current_resolution["soporte_magnetico"] = None
                    resolutions.append(current_resolution)
                
                match = re.search(r'Resolución\s+(?:No\.?\s*)?(\d+(?:\s+\d+)?)', text, re.IGNORECASE)
                resolution_number = None
                if match:
                    resolution_number = match.group(1).replace(' ', '')
                
                date_match = re.search(
                    r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',
                    text,
                    re.IGNORECASE
                )
                resolution_date = None
                if date_match:
                    month_num = month_to_number(date_match.group(2))
                    resolution_date = f"{date_match.group(3)}-{str(month_num).zfill(2)}-{date_match.group(1).zfill(2)}"
                
                if not resolution_number:
                    resolution_number_match = re.search(r'(\d{5,})', text)
                    if resolution_number_match:
                        resolution_number = resolution_number_match.group(1)
                
                current_resolution = {
                    "number": resolution_number,
                    "date": resolution_date,
                    "url": full_url,
                    "title": text,
                    "soporte_magnetico": []
                }
            
            elif is_soporte_magnetico:
                soporte = {
                    "title": text,
                    "url": full_url
                }
                
                if current_resolution:
                    current_resolution["soporte_magnetico"].append(soporte)
                else:
                    resolution_number_from_soporte = None
                    soporte_text_match = re.search(r'resolución\s+(\d+(?:\s+\d+)?)', text_lower, re.IGNORECASE)
                    if soporte_text_match:
                        resolution_number_from_soporte = soporte_text_match.group(1).replace(' ', '')
                    
                    target_resolution = None
                    
                    if resolution_number_from_soporte:
                        for res in resolutions:
                            if res.get("number") == resolution_number_from_soporte:
                                target_resolution = res
                                break
                    
                    if target_resolution:
                        if not target_resolution.get("soporte_magnetico"):
                            target_resolution["soporte_magnetico"] = []
                        target_resolution["soporte_magnetico"].append(soporte)
                    else:
                        logger.warning(f"[web_scraper] Soporte magnético sin resolución correspondiente: {text}")
        
        if current_resolution:
            if not current_resolution.get("soporte_magnetico") or len(current_resolution.get("soporte_magnetico", [])) == 0:
                current_resolution["soporte_magnetico"] = None
            resolutions.append(current_resolution)
            
        for resolution in resolutions:
            if isinstance(resolution.get("soporte_magnetico"), list):
                if len(resolution["soporte_magnetico"]) == 0:
                    resolution["soporte_magnetico"] = None
            
    except Exception as e:
        logger.error(f"[web_scraper] Error extrayendo resoluciones del acordeón: {e}")
        traceback.print_exc()
        raise
    
    return resolutions


def extract_plantillas_from_accordion(accordion_body, base_url: str) -> List[Dict[str, Any]]:
    """
    Extrae plantillas desde un elemento accordion-body.
    
    Args:
        accordion_body: Elemento BeautifulSoup del accordion-body
        base_url: URL base
        
    Returns:
        Lista de plantillas
    """
    plantillas = []
    
    try:
        all_links = accordion_body.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if not href or not text:
                continue
            
            full_url = urljoin(base_url, href)
            text_lower = text.lower()
            
            if ("plantilla" in text_lower or ".xls" in href.lower() or ".xlsx" in href.lower() or ".xlsm" in href.lower()) and \
               ("operador" in text_lower or "asociado" in text_lower):
                
                plantilla_type = None
                if "operador" in text_lower:
                    plantilla_type = "OPERADOR"
                elif "asociado" in text_lower:
                    plantilla_type = "ASOCIADO"
                
                plantillas.append({
                    "type": plantilla_type,
                    "title": text,
                    "url": full_url
                })
                
    except Exception as e:
        logger.error(f"[web_scraper] Error extrayendo plantillas del acordeón: {e}")
    
    return plantillas


def extract_resolutions_from_links(all_links, period_pattern: str, base_url: str) -> List[Dict[str, Any]]:
    """
    Extrae resoluciones desde una lista de enlaces (método alternativo).
    
    Args:
        all_links: Lista de elementos <a> de BeautifulSoup
        period_pattern: Patrón del período
        base_url: URL base
        
    Returns:
        Lista de resoluciones
    """
    resolutions = []
    
    try:
        resolutions_dict = {}
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if not href or not text:
                continue
            
            parent = link.parent
            parent_text = ""
            for _ in range(10):
                if parent:
                    parent_text = parent.get_text()
                    if period_pattern in parent_text:
                        break
                    parent = parent.parent
                else:
                    break
            
            if period_pattern not in parent_text:
                continue
            
            full_url = urljoin(base_url, href)
            text_lower = text.lower()
            
            if "resolución" in text_lower or "resolucion" in text_lower:
                match = re.search(r'Resolución\s+No\.?\s*(\d+)', text, re.IGNORECASE)
                if match:
                    resolution_number = match.group(1)
                    
                    date_match = re.search(
                        r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',
                        text,
                        re.IGNORECASE
                    )
                    resolution_date = None
                    if date_match:
                        month_num = month_to_number(date_match.group(2))
                        resolution_date = f"{date_match.group(3)}-{month_num}-{date_match.group(1).zfill(2)}"
                    
                    resolutions_dict[resolution_number] = {
                        "number": resolution_number,
                        "date": resolution_date,
                        "url": full_url,
                        "title": text,
                        "soporte_magnetico": None
                    }
            
            elif (".xls" in href.lower() or ".xlsx" in href.lower() or ".xlsm" in href.lower()) or \
                 ("soporte magnético" in text_lower or "soporte magnetico" in text_lower):
                
                excel_url = full_url
                excel_title = text if text else href.split("/")[-1]
                
                resolution_number = find_nearest_resolution(link, resolutions_dict)
                
                if resolution_number and resolution_number in resolutions_dict:
                    resolutions_dict[resolution_number]["soporte_magnetico"] = {
                        "title": excel_title,
                        "url": excel_url
                    }
                else:
                    resolutions_dict[f"excel_{len(resolutions_dict)}"] = {
                        "number": None,
                        "date": None,
                        "url": None,
                        "title": None,
                        "soporte_magnetico": {
                            "title": excel_title,
                            "url": excel_url
                        }
                    }
        
        resolutions = list(resolutions_dict.values())
        
    except Exception as e:
        logger.error(f"[web_scraper] Error extrayendo resoluciones de enlaces: {e}")
        traceback.print_exc()
        raise
    
    return resolutions


def find_nearest_resolution(link, resolutions_dict: Dict) -> str:
    """
    Encuentra el número de resolución más cercano a un enlace.
    
    Args:
        link: Elemento BeautifulSoup del enlace
        resolutions_dict: Diccionario de resoluciones
        
    Returns:
        Número de resolución o None
    """
    try:
        parent = link.parent
        parent_text = ""
        for _ in range(15):
            if parent:
                parent_text = parent.get_text()
                for resolution_number in resolutions_dict.keys():
                    if resolution_number and resolution_number in parent_text:
                        return resolution_number
                parent = parent.parent
            else:
                break
        return None
    except Exception:
        return None