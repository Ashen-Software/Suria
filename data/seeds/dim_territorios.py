"""
Seed para poblar la tabla dim_territorios con municipios de Colombia.

Obtiene datos desde la API de Socrata (datos.gov.co) con información de
departamentos, municipios, coordenadas y códigos DIVIPOLA.

Uso:
    python -m seeds.dim_territorios
    
    # Modo dry-run (solo muestra qué haría):
    python -m seeds.dim_territorios --dry-run
    
    # Con token personalizado:
    python -m seeds.dim_territorios --token YOUR_APP_TOKEN
"""
import argparse
import os
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.backend_client import BackendClient
from logs_config.logger import app_logger as logger


# API de Socrata - Municipios de Colombia (datos.gov.co)
SOCRATA_API_URL = "https://www.datos.gov.co/api/v3/views/vafm-j2df/query.json"


@dataclass
class TerritorioRecord:
    """Registro para dim_territorios."""
    departamento: str
    municipio: str
    latitud: Optional[float]
    longitud: Optional[float]
    divipola: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para inserción en DB."""
        return {
            "departamento": self.departamento,
            "municipio": self.municipio,
            "latitud": self.latitud,
            "longitud": self.longitud,
            "divipola": self.divipola
        }


def fetch_territorios_from_api(app_token: Optional[str] = None, timeout: int = 120) -> List[Dict[str, Any]]:
    """
    Obtiene datos de territorios desde la API de Socrata.
    
    Args:
        app_token: Token de aplicación de Socrata (opcional pero recomendado)
        timeout: Timeout para la petición HTTP
    
    Returns:
        Lista de diccionarios con datos crudos de la API
    """
    params = {}
    
    # Agregar token si está disponible
    if app_token:
        params["app_token"] = app_token
    else:
        # Intentar obtener de variable de entorno
        env_token = os.getenv("DATOS_GOV_TOKEN")
        if env_token:
            params["app_token"] = env_token
    
    headers = {
        "Accept": "application/json"
    }
    
    logger.info(f"[Seed dim_territorios] Consultando API: {SOCRATA_API_URL}")
    
    try:
        response = requests.get(
            SOCRATA_API_URL,
            params=params,
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Socrata retorna datos en {"data": [...], "columns": [...], ...}
        if isinstance(data, dict) and "data" in data:
            rows = data.get("data", [])
            logger.info(f"[Seed dim_territorios] {len(rows)} registros obtenidos de la API")
            return rows
        elif isinstance(data, list):
            logger.info(f"[Seed dim_territorios] {len(data)} registros obtenidos de la API")
            return data
        else:
            logger.warning(f"[Seed dim_territorios] Formato de respuesta inesperado: {type(data)}")
            return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"[Seed dim_territorios] Error consultando API: {e}")
        raise


def parse_territorio_record(raw_record: Dict[str, Any]) -> Optional[TerritorioRecord]:
    """
    Parsea un registro crudo de la API a TerritorioRecord.
    
    La API retorna columnas como:
    - cod_dpto: Código departamento
    - nom_dpto: Nombre departamento  
    - cod_mpio: Código municipio
    - nom_mpio: Nombre municipio
    - latitud: Latitud
    - longitud: Longitud
    
    El codigo DIVIPOLA es la concatenación de cod_dpto + cod_mpio
    """
    try:
        # Extraer campos - la API puede retornar en mayúsculas o minúsculas
        cod_dpto = raw_record.get("cod_dpto") or raw_record.get("COD_DPTO")
        nom_dpto = raw_record.get("nom_dpto") or raw_record.get("NOM_DPTO")
        cod_mpio = raw_record.get("cod_mpio") or raw_record.get("COD_MPIO")
        nom_mpio = raw_record.get("nom_mpio") or raw_record.get("NOM_MPIO")
        latitud = raw_record.get("latitud") or raw_record.get("LATITUD")
        longitud = raw_record.get("longitud") or raw_record.get("LONGITUD")
        
        # Validar campos obligatorios
        if not nom_dpto or not nom_mpio:
            logger.debug(f"[Seed dim_territorios] Registro sin departamento/municipio: {raw_record}")
            return None
        
        # Limpiar y normalizar nombres
        departamento = str(nom_dpto).strip().upper()
        municipio = str(nom_mpio).strip().upper()
        
        # Construir codigo DIVIPOLA (5 digitos: 2 depto + 3 municipio)
        divipola = None
        if cod_dpto is not None and cod_mpio is not None:
            try:
                divipola = f"{int(cod_dpto):02d}{int(cod_mpio):03d}"
            except (ValueError, TypeError):
                # Si no se puede convertir, concatenar como strings
                divipola = f"{cod_dpto}{cod_mpio}"
        
        # Parsear coordenadas
        lat = None
        lon = None
        
        if latitud is not None:
            try:
                lat = float(latitud)
            except (ValueError, TypeError):
                pass
                
        if longitud is not None:
            try:
                lon = float(longitud)
            except (ValueError, TypeError):
                pass
        
        return TerritorioRecord(
            departamento=departamento,
            municipio=municipio,
            latitud=lat,
            longitud=lon,
            divipola=divipola
        )
        
    except Exception as e:
        logger.warning(f"[Seed dim_territorios] Error parseando registro: {e}")
        return None


def generate_territorio_records(raw_data: List[Dict[str, Any]]) -> List[TerritorioRecord]:
    """
    Genera lista de TerritorioRecord a partir de datos crudos de la API.
    Elimina duplicados basándose en (departamento, municipio).
    """
    records = []
    seen = set()  # Para evitar duplicados
    
    for raw in raw_data:
        record = parse_territorio_record(raw)
        if record:
            key = (record.departamento, record.municipio)
            if key not in seen:
                seen.add(key)
                records.append(record)
    
    logger.info(f"[Seed dim_territorios] {len(records)} registros únicos generados (de {len(raw_data)} totales)")
    return records


def seed_dim_territorios(
    app_token: Optional[str] = None,
    batch_size: int = 100,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Puebla la tabla dim_territorios con datos de municipios de Colombia.
    
    Args:
        app_token: Token de aplicación de Socrata (opcional)
        batch_size: Tamaño de lote para inserciones
        dry_run: Si True, solo muestra qué haría sin insertar
    
    Returns:
        Diccionario con estadísticas de la operación
    """
    logger.info("[Seed dim_territorios] Iniciando proceso de seed")
    
    # Obtener datos de la API
    try:
        raw_data = fetch_territorios_from_api(app_token)
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error obteniendo datos de la API: {e}"
        }
    
    if not raw_data:
        return {
            "status": "error",
            "error": "No se obtuvieron datos de la API"
        }
    
    # Generar registros
    records = generate_territorio_records(raw_data)
    total_records = len(records)
    
    if total_records == 0:
        return {
            "status": "error",
            "error": "No se pudieron parsear registros válidos"
        }
    
    logger.info(f"[Seed dim_territorios] {total_records} territorios a insertar")
    
    # Contar departamentos únicos
    departamentos = set(r.departamento for r in records)
    logger.info(f"[Seed dim_territorios] {len(departamentos)} departamentos únicos")
    
    if dry_run:
        logger.info("[Seed dim_territorios] Modo DRY RUN - no se insertarán datos")
        # Mostrar algunos ejemplos
        logger.info("Ejemplos de registros:")
        for r in records[:5]:
            logger.info(f"  {r.to_dict()}")
        if len(records) > 5:
            logger.info("  ...")
            for r in records[-3:]:
                logger.info(f"  {r.to_dict()}")
        
        return {
            "status": "dry_run",
            "total_from_api": len(raw_data),
            "total_unique": total_records,
            "departamentos": len(departamentos),
            "inserted": 0,
            "skipped": 0,
            "errors": 0
        }
    
    # Inicializar cliente
    client = BackendClient()
    
    if not client.client:
        logger.error("[Seed dim_territorios] No se pudo conectar a Supabase")
        return {
            "status": "error",
            "error": "No se pudo conectar a Supabase"
        }
    
    # Insertar en lotes con upsert
    inserted = 0
    skipped = 0
    errors = 0
    
    for i in range(0, total_records, batch_size):
        batch = records[i:i + batch_size]
        batch_dicts = [r.to_dict() for r in batch]
        
        try:
            # Usar upsert con on_conflict para ignorar duplicados
            # La constraint UNIQUE es sobre (departamento, municipio)
            response = client.client.table("dim_territorios").upsert(
                batch_dicts,
                on_conflict="departamento,municipio"
            ).execute()
            
            if response.data:
                inserted += len(response.data)
            
            logger.debug(f"[Seed dim_territorios] Lote {i//batch_size + 1}: {len(batch)} registros procesados")
            
        except Exception as e:
            error_msg = str(e)
            
            if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
                logger.debug(f"[Seed dim_territorios] Lote {i//batch_size + 1} tiene duplicados, procesando individualmente")
                
                for record in batch:
                    try:
                        client.client.table("dim_territorios").upsert(
                            record.to_dict(),
                            on_conflict="departamento,municipio"
                        ).execute()
                        inserted += 1
                    except Exception as e2:
                        if "duplicate" in str(e2).lower():
                            skipped += 1
                        else:
                            errors += 1
                            logger.warning(f"[Seed dim_territorios] Error insertando {record.municipio}, {record.departamento}: {e2}")
            else:
                errors += len(batch)
                logger.error(f"[Seed dim_territorios] Error en lote {i//batch_size + 1}: {e}")
    
    logger.info(f"[Seed dim_territorios] Completado: {inserted} insertados, {skipped} omitidos (duplicados), {errors} errores")
    
    return {
        "status": "success" if errors == 0 else "partial",
        "total_from_api": len(raw_data),
        "total_unique": total_records,
        "departamentos": len(departamentos),
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors
    }


def main():
    """Punto de entrada CLI."""
    parser = argparse.ArgumentParser(
        description="Poblar tabla dim_territorios con municipios de Colombia desde API Socrata"
    )
    parser.add_argument(
        "--token", "-t",
        type=str,
        default=None,
        help="Token de aplicación de Socrata (o usar env var DATOS_GOV_TOKEN)"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=100,
        help="Tamaño de lote para inserciones (default: 100)"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Solo mostrar qué haría sin insertar datos"
    )
    
    args = parser.parse_args()
    
    # Ejecutar seed
    result = seed_dim_territorios(
        app_token=args.token,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )
    
    # Mostrar resumen
    print("\n" + "="*50)
    print("RESUMEN SEED dim_territorios")
    print("="*50)
    print(f"Estado: {result.get('status', 'unknown')}")
    
    if result.get("error"):
        print(f"Error: {result.get('error')}")
    else:
        print(f"Registros de API: {result.get('total_from_api', 0)}")
        print(f"Registros únicos: {result.get('total_unique', 0)}")
        print(f"Departamentos: {result.get('departamentos', 0)}")
        print(f"Insertados: {result.get('inserted', 0)}")
        print(f"Omitidos (duplicados): {result.get('skipped', 0)}")
        print(f"Errores: {result.get('errors', 0)}")
    
    print("="*50)
    
    return 0 if result.get("status") in ["success", "dry_run"] else 1


if __name__ == "__main__":
    exit(main())
