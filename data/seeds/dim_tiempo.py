"""
Seed para poblar la tabla dim_tiempo con registros mensuales.

Genera registros desde un año inicial hasta un año final, marcando
como es_proyeccion=True los meses que superan la fecha actual.

Uso:
    python -m seeds.dim_tiempo --start-year 2010 --end-year 2036
    
    # O con valores por defecto (2010-2036):
    python -m seeds.dim_tiempo
"""
import argparse
from datetime import date, datetime
from typing import List, Dict, Any
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.backend_client import BackendClient
from logs_config.logger import app_logger as logger


# Mapeo de numero de mes a nombre en español
NOMBRES_MESES = {
    1: "Enero",
    2: "Febrero", 
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}


@dataclass
class TiempoRecord:
    """Registro para dim_tiempo."""
    fecha: date
    anio: int
    mes: int
    nombre_mes: str
    es_proyeccion: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para inserción en DB."""
        return {
            "fecha": self.fecha.isoformat(),
            "anio": self.anio,
            "mes": self.mes,
            "nombre_mes": self.nombre_mes,
            "es_proyeccion": self.es_proyeccion
        }


def generate_tiempo_records(
    start_year: int,
    end_year: int,
    reference_date: date = None
) -> List[TiempoRecord]:
    """
    Genera registros de tiempo para el rango de años especificado.
    
    Args:
        start_year: Año inicial (inclusive)
        end_year: Año final (inclusive)
        reference_date: Fecha de referencia para determinar proyección.
                       Si None, usa la fecha actual.
    
    Returns:
        Lista de TiempoRecord
    """
    if reference_date is None:
        reference_date = date.today()
    
    records = []
    
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            fecha = date(year, month, 1)
            
            # Es proyeccion si la fecha es posterior al mes actual
            es_proyeccion = fecha > date(reference_date.year, reference_date.month, 1)
            
            record = TiempoRecord(
                fecha=fecha,
                anio=year,
                mes=month,
                nombre_mes=NOMBRES_MESES[month],
                es_proyeccion=es_proyeccion
            )
            records.append(record)
    
    return records


def seed_dim_tiempo(
    start_year: int = 2010,
    end_year: int = 2036,
    batch_size: int = 100,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Puebla la tabla dim_tiempo con registros mensuales.
    
    Args:
        start_year: Año inicial
        end_year: Año final
        batch_size: Tamaño de lote para inserciones
        dry_run: Si True, solo muestra qué haría sin insertar
    
    Returns:
        Diccionario con estadísticas de la operación
    """
    logger.info(f"[Seed dim_tiempo] Generando registros desde {start_year} hasta {end_year}")
    
    # Generar registros
    records = generate_tiempo_records(start_year, end_year)
    total_records = len(records)
    
    logger.info(f"[Seed dim_tiempo] {total_records} registros generados")
    
    # Contar proyecciones
    proyecciones = sum(1 for r in records if r.es_proyeccion)
    historicos = total_records - proyecciones
    
    logger.info(f"[Seed dim_tiempo] {historicos} históricos, {proyecciones} proyecciones")
    
    if dry_run:
        logger.info("[Seed dim_tiempo] Modo DRY RUN - no se insertarán datos")
        # Mostrar algunos ejemplos
        logger.info("Ejemplos de registros:")
        for r in records[:3]:
            logger.info(f"  {r.to_dict()}")
        logger.info("  ...")
        for r in records[-3:]:
            logger.info(f"  {r.to_dict()}")
        
        return {
            "status": "dry_run",
            "total_generated": total_records,
            "historicos": historicos,
            "proyecciones": proyecciones,
            "inserted": 0,
            "skipped": 0,
            "errors": 0
        }
    
    # Inicializar cliente
    client = BackendClient()
    
    if not client.client:
        logger.error("[Seed dim_tiempo] No se pudo conectar a Supabase")
        return {
            "status": "error",
            "error": "No se pudo conectar a Supabase"
        }
    
    # Insertar en lotes con upsert (ignorar duplicados)
    inserted = 0
    skipped = 0
    errors = 0
    
    for i in range(0, total_records, batch_size):
        batch = records[i:i + batch_size]
        batch_dicts = [r.to_dict() for r in batch]
        
        try:
            # Usar upsert con on_conflict para ignorar duplicados (fecha es UNIQUE)
            response = client.client.table("dim_tiempo").upsert(
                batch_dicts,
                on_conflict="fecha"  # Columna con constraint UNIQUE
            ).execute()
            
            # Contar inserciones exitosas
            if response.data:
                inserted += len(response.data)
            
            logger.debug(f"[Seed dim_tiempo] Lote {i//batch_size + 1}: {len(batch)} registros procesados")
            
        except Exception as e:
            error_msg = str(e)
            
            # Si el error es por duplicado, intentar uno por uno
            if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
                logger.debug(f"[Seed dim_tiempo] Lote {i//batch_size + 1} tiene duplicados, procesando individualmente")
                
                for record in batch:
                    try:
                        client.client.table("dim_tiempo").upsert(
                            record.to_dict(),
                            on_conflict="fecha"
                        ).execute()
                        inserted += 1
                    except Exception as e2:
                        if "duplicate" in str(e2).lower():
                            skipped += 1
                        else:
                            errors += 1
                            logger.warning(f"[Seed dim_tiempo] Error insertando {record.fecha}: {e2}")
            else:
                errors += len(batch)
                logger.error(f"[Seed dim_tiempo] Error en lote {i//batch_size + 1}: {e}")
    
    logger.info(f"[Seed dim_tiempo] Completado: {inserted} insertados, {skipped} omitidos (ya existían), {errors} errores")
    
    return {
        "status": "success" if errors == 0 else "partial",
        "total_generated": total_records,
        "historicos": historicos,
        "proyecciones": proyecciones,
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors
    }


def main():
    """Punto de entrada CLI."""
    parser = argparse.ArgumentParser(
        description="Poblar tabla dim_tiempo con registros mensuales"
    )
    parser.add_argument(
        "--start-year", "-s",
        type=int,
        default=2010,
        help="Año inicial (default: 2010)"
    )
    parser.add_argument(
        "--end-year", "-e", 
        type=int,
        default=2036,
        help="Año final (default: 2036)"
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
    
    # Validaciones
    if args.start_year > args.end_year:
        logger.error(f"El año inicial ({args.start_year}) no puede ser mayor que el final ({args.end_year})")
        return 1
    
    if args.start_year < 1900 or args.end_year > 2100:
        logger.error("Los años deben estar entre 1900 y 2100")
        return 1
    
    # Ejecutar seed
    result = seed_dim_tiempo(
        start_year=args.start_year,
        end_year=args.end_year,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )
    
    # Mostrar resumen
    print("\n" + "="*50)
    print("RESUMEN SEED dim_tiempo")
    print("="*50)
    print(f"Estado: {result.get('status', 'unknown')}")
    print(f"Registros generados: {result.get('total_generated', 0)}")
    print(f"  - Históricos: {result.get('historicos', 0)}")
    print(f"  - Proyecciones: {result.get('proyecciones', 0)}")
    print(f"Insertados: {result.get('inserted', 0)}")
    print(f"Omitidos (duplicados): {result.get('skipped', 0)}")
    print(f"Errores: {result.get('errors', 0)}")
    print("="*50)
    
    return 0 if result.get("status") in ["success", "dry_run"] else 1


if __name__ == "__main__":
    exit(main())
