"""
Test para el loader de fact_regalias.

Genera 100 registros de prueba y los carga usando FactLoader.

Uso:
    python -m workflows.full_etl.tests.test_loader
    
    # Solo ver qué haría (dry-run)
    python -m workflows.full_etl.tests.test_loader --dry-run
    
    # Con más o menos registros
    python -m workflows.full_etl.tests.test_loader --count 50
"""
import argparse
import random
from datetime import date
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from logs_config.logger import app_logger as logger


# Datos de prueba
CAMPOS_EJEMPLO = [
    "APIAY", "CASTILLA", "CHICHIMENE", "RUBIALES", "QUIFA",
    "CUPIAGUA", "CUSIANA", "PAUTO", "FLOREÑA", "RECETOR",
    "OCELOTE", "JAGUAR", "CARACARA", "RANCHO HERMOSO", "LA CIRA",
    "YARIGUI", "CASABE", "TISQUIRAMA", "MORICHE", "TOCA",
]

DEPARTAMENTOS = [
    ("META", "ACACIAS"),
    ("META", "CASTILLA LA NUEVA"),
    ("META", "PUERTO GAITAN"),
    ("CASANARE", "AGUAZUL"),
    ("CASANARE", "TAURAMENA"),
    ("CASANARE", "YOPAL"),
    ("SANTANDER", "BARRANCABERMEJA"),
    ("HUILA", "NEIVA"),
    ("ARAUCA", "ARAUCA"),
    ("BOYACA", "PUERTO BOYACA"),
]

CONTRATOS = [
    "E&P-001", "E&P-002", "E&P-003", "ASOCIACION-01", "ASOCIACION-02",
    "TEA-001", "TEA-002", "BLOQUE-A", "BLOQUE-B", "BLOQUE-C",
]

TIPOS_PRODUCCION = ["ASOCIADOS", "DIRECTA", "REGALIAS"]
TIPOS_HIDROCARBURO = ["G", "O"]  # G=Gas, O=Petróleo


def generate_test_records(count: int = 100) -> List[Dict[str, Any]]:
    """
    Genera registros de prueba en el formato que produce el transformer.
    
    Args:
        count: Número de registros a generar
        
    Returns:
        Lista de registros en formato transformer output
    """
    records = []
    
    # Usar fechas de 2020-2024 para asegurar que existan en dim_tiempo
    years = list(range(2020, 2025))
    months = list(range(1, 13))
    
    for i in range(count):
        # Seleccionar datos aleatorios
        campo = random.choice(CAMPOS_EJEMPLO) + f"_{i % 20}"  # Agregar sufijo para variedad
        depto, muni = random.choice(DEPARTAMENTOS)
        contrato = random.choice(CONTRATOS)
        tipo_prod = random.choice(TIPOS_PRODUCCION)
        tipo_hidro = random.choice(TIPOS_HIDROCARBURO)
        
        year = random.choice(years)
        month = random.choice(months)
        fecha = date(year, month, 1)
        
        # Generar valores numéricos aleatorios
        precio_usd = round(random.uniform(30, 100), 2)
        porcentaje_regalia = round(random.uniform(5, 25), 2)
        produccion_gravable = round(random.uniform(1000, 50000), 2)
        volumen_regalia = round(produccion_gravable * porcentaje_regalia / 100, 2)
        valor_regalias_cop = round(volumen_regalia * precio_usd * 4000, 2)  # Asumiendo TRM ~4000
        
        # Estructura que produce el transformer
        record = {
            "fact_table": "fact_regalias",
            "data": {
                "tiempo_fecha": fecha,
                "campo_nombre": campo,
                "departamento": depto,
                "municipio": muni,
                "latitud": round(random.uniform(4.0, 7.0), 6),
                "longitud": round(random.uniform(-75.0, -71.0), 6),
                "contrato": contrato,
                "tipo_produccion": tipo_prod,
                "tipo_hidrocarburo": tipo_hidro,
                "precio_usd": precio_usd,
                "porcentaje_regalia": porcentaje_regalia,
                "produccion_gravable": produccion_gravable,
                "volumen_regalia": volumen_regalia,
                "valor_regalias_cop": valor_regalias_cop,
                "unidad": "Bls/Kpc",
            },
            "dimensions": {
                "tiempo": {
                    "fecha": fecha,
                    "anio": year,
                    "mes": month,
                    "es_proyeccion": False,
                },
                "territorio": {
                    "departamento": depto,
                    "municipio": muni,
                },
                "campo": {
                    "nombre_campo": campo,
                    "contrato": contrato,
                    "activo": True,
                },
            }
        }
        
        records.append(record)
    
    return records


def run_test(count: int = 100, dry_run: bool = False):
    """
    Ejecuta el test del loader.
    
    Args:
        count: Número de registros a generar
        dry_run: Si True, solo muestra qué haría sin insertar
    """
    print("="*60)
    print("TEST: FactLoader con registros de prueba")
    print("="*60)
    
    # Generar registros
    print(f"\n1. Generando {count} registros de prueba...")
    records = generate_test_records(count)
    print(f"   ✓ {len(records)} registros generados")
    
    # Mostrar ejemplos
    print("\n2. Ejemplos de registros generados:")
    for i, r in enumerate(records[:3]):
        data = r["data"]
        print(f"   [{i+1}] {data['campo_nombre']} | {data['tiempo_fecha']} | "
              f"{data['tipo_hidrocarburo']} | ${data['precio_usd']:.2f}")
    print("   ...")
    
    if dry_run:
        print("\n3. [DRY RUN] No se insertarán datos")
        print("   Para ejecutar realmente, omite --dry-run")
        return
    
    # Importar loader
    print("\n3. Cargando FactLoader...")
    try:
        from workflows.full_etl.loaders import FactLoader
        loader = FactLoader(batch_size=50)
        print("   ✓ FactLoader inicializado")
    except Exception as e:
        print(f"   ✗ Error importando FactLoader: {e}")
        return
    
    # Ejecutar carga
    print(f"\n4. Ejecutando carga de {count} registros...")
    try:
        result = loader.load(records, "api_regalias")
        
        print("\n5. Resultado:")
        print(f"   Status: {result.get('status')}")
        
        stats = result.get("stats", {})
        print(f"   - Total procesados: {stats.get('total_processed', 0)}")
        print(f"   - Insertados: {stats.get('inserted', 0)}")
        print(f"   - Sin tiempo_id: {stats.get('skipped_no_tiempo', 0)}")
        print(f"   - Sin campo_id: {stats.get('skipped_no_campo', 0)}")
        print(f"   - Errores: {stats.get('errors', 0)}")
        
        resolver_stats = result.get("resolver_stats", {})
        if resolver_stats:
            print(f"\n   Resolver stats:")
            print(f"   - Tiempo lookups: {resolver_stats.get('tiempo_lookups', 0)} "
                  f"(cache hits: {resolver_stats.get('tiempo_cache_hits', 0)})")
            print(f"   - Territorio lookups: {resolver_stats.get('territorio_lookups', 0)} "
                  f"(cache hits: {resolver_stats.get('territorio_cache_hits', 0)})")
            print(f"   - Campo lookups: {resolver_stats.get('campo_lookups', 0)} "
                  f"(cache hits: {resolver_stats.get('campo_cache_hits', 0)})")
            print(f"   - Campos creados: {resolver_stats.get('campo_inserts', 0)}")
        
        # Mostrar errores si hay
        error_details = result.get("error_details", [])
        if error_details:
            print(f"\n   Primeros errores:")
            for err in error_details[:5]:
                print(f"   - {err}")
                
    except Exception as e:
        print(f"   ✗ Error en carga: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description="Test del FactLoader")
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=100,
        help="Número de registros a generar (default: 100)"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Solo mostrar qué haría sin insertar datos"
    )
    
    args = parser.parse_args()
    run_test(count=args.count, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
