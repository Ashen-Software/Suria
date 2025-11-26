"""
Loader para tablas de hechos (fact tables).

Gestiona la inserción de registros transformados a fact_regalias
con FKs ya resueltas por DimensionResolver.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from common.sanitizers import sanitize_value
from services.backend_client import BackendClient
from logs_config.logger import app_logger as logger
from .base import BaseLoader
from .dimension_resolver import DimensionResolver


class FactLoader(BaseLoader):
    """
    Carga registros transformados a tablas de hechos (fact_regalias, etc.).
    
    Resuelve FKs usando DimensionResolver antes de insertar.
    """
    
    # Mapeo de campos del transformer a columnas de fact_regalias
    REGALIAS_COLUMN_MAPPING = {
        # fact_column: data_field
        "tipo_produccion": "tipo_produccion",
        "tipo_hidrocarburo": "tipo_hidrocarburo",
        "precio_usd": "precio_usd",
        "porcentaje_regalia": "porcentaje_regalia",
        "produccion_gravable": "produccion_gravable",
        "volumen_regalia": "volumen_regalia",
        "unidad": "unidad",
        "valor_regalias_cop": "valor_regalias_cop",
    }
    
    def __init__(
        self, 
        client: Optional[BackendClient] = None,
        dimension_resolver: Optional[DimensionResolver] = None,
        batch_size: int = 10000
    ):
        """
        Inicializa el loader.
        
        Args:
            client: BackendClient opcional
            dimension_resolver: DimensionResolver opcional
            batch_size: Tamaño de lote para inserciones
        """
        self.client = client or BackendClient()
        self.resolver = dimension_resolver or DimensionResolver(self.client)
        self.batch_size = batch_size
        
        # Estadisticas
        self.stats = {
            "total_processed": 0,
            "inserted": 0,
            "skipped_no_tiempo": 0,
            "skipped_no_campo": 0,
            "errors": 0,
        }
    
    def load(self, records: List[Dict[str, Any]], source_id: str) -> Dict[str, Any]:
        """
        Carga registros transformados a fact_regalias.
        
        Args:
            records: Lista de registros (salida del transformer)
            source_id: ID de la fuente
            
        Returns:
            Estadísticas de la carga
        """
        if not records:
            return self._result("success", "No hay registros para cargar")
        
        logger.info(f"[FactLoader] Iniciando carga de {len(records)} registros para {source_id}")
        
        # Pre-cargar caches para optimizar
        logger.info("[FactLoader] Pre-cargando caches de dimensiones...")
        cache_stats = self.resolver.preload_all_caches()
        logger.info(f"[FactLoader] Caches cargados: {cache_stats}")
        
        # Procesar registros
        fact_records = []
        error_details = []
        total_records = len(records)
        progress_interval = 10000  # Log cada 10k registros
        
        logger.info(f"[FactLoader] Preparando {total_records} registros...")
        
        for i, record in enumerate(records):
            self.stats["total_processed"] += 1
            
            # Log de progreso cada N registros
            if (i + 1) % progress_interval == 0:
                logger.info(f"[FactLoader] Progreso: {i + 1}/{total_records} registros preparados ({len(fact_records)} válidos)")
            
            try:
                fact_record = self._prepare_fact_record(record, source_id)
                
                if fact_record is None:
                    continue  # Ya se actualizo stats en _prepare_fact_record
                
                fact_records.append(fact_record)
                
            except Exception as e:
                self.stats["errors"] += 1
                error_details.append({
                    "index": i,
                    "error": str(e),
                    "record": record.get("data", {}).get("campo_nombre", "unknown")
                })
                logger.warning(f"[FactLoader] Error preparando registro {i}: {e}")
        
        logger.info(f"[FactLoader] Preparación completada: {len(fact_records)} registros válidos de {total_records}")
        
        # Insertar en lotes
        if fact_records:
            insert_result = self._batch_insert(fact_records, source_id)
            self.stats["inserted"] = insert_result.get("inserted", 0)
            self.stats["errors"] += insert_result.get("errors", 0)
            error_details.extend(insert_result.get("error_details", []))
        
        # Resultado final
        status = "success" if self.stats["errors"] == 0 else "partial"
        if self.stats["inserted"] == 0 and self.stats["errors"] > 0:
            status = "error"
        
        # Log resumen de operaciones del resolver
        self.resolver.log_summary()
        
        result = self._result(status)
        result["error_details"] = error_details
        result["resolver_stats"] = self.resolver.get_stats()
        
        logger.info(
            f"[FactLoader] Carga completada: {self.stats['inserted']} insertados, "
            f"{self.stats['skipped_no_tiempo']} sin tiempo, "
            f"{self.stats['skipped_no_campo']} sin campo, "
            f"{self.stats['errors']} errores"
        )
        
        return result
    
    def _prepare_fact_record(
        self, 
        record: Dict[str, Any], 
        source_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Prepara un registro para inserción en fact_regalias.
        
        Resuelve FKs y mapea campos.
        
        Returns:
            Dict listo para INSERT, o None si faltan FKs críticas
        """
        # Resolver FKs
        fks = self.resolver.resolve_all_for_record(record)
        
        # Validar FKs criticas
        if fks["tiempo_id"] is None:
            self.stats["skipped_no_tiempo"] += 1
            data = record.get("data", {})
            logger.debug(
                f"[FactLoader] Registro omitido por falta de tiempo_id. "
                f"Fecha: {data.get('tiempo_fecha')}"
            )
            return None
        
        if fks["campo_id"] is None:
            self.stats["skipped_no_campo"] += 1
            data = record.get("data", {})
            logger.debug(
                f"[FactLoader] Registro omitido por falta de campo_id. "
                f"Campo: {data.get('campo_nombre')}"
            )
            return None
        
        # Construir registro para fact table
        data = record.get("data", {})
        
        fact_record = {
            "tiempo_id": fks["tiempo_id"],
            "campo_id": fks["campo_id"],
            "source_id": source_id,
        }
        
        # Mapear campos del transformer
        for fact_col, data_field in self.REGALIAS_COLUMN_MAPPING.items():
            value = data.get(data_field)
            if value is not None:
                # Limpiar valores numéricos
                if fact_col in ["precio_usd", "porcentaje_regalia", "produccion_gravable", 
                               "volumen_regalia", "valor_regalias_cop"]:
                    try:
                        value = float(value) if value != "" else None
                    except (ValueError, TypeError):
                        value = None
                
                # Sanitizar NaN/Inf (PostgreSQL JSON no los acepta)
                value = sanitize_value(value)
                
                if value is not None:
                    fact_record[fact_col] = value
        
        return fact_record
    
    def _batch_insert(
        self, 
        records: List[Dict[str, Any]], 
        source_id: str
    ) -> Dict[str, Any]:
        """
        Inserta registros en lotes.
        
        Returns:
            Dict con estadísticas de inserción
        """
        if not self.client.client:
            logger.error("[FactLoader] Cliente no disponible para inserción")
            return {"inserted": 0, "errors": len(records), "error_details": []}
        
        inserted = 0
        errors = 0
        error_details = []
        
        total_batches = (len(records) + self.batch_size - 1) // self.batch_size
        logger.info(f"[FactLoader] Insertando {len(records)} registros en {total_batches} lotes (batch_size={self.batch_size})")
        
        for batch_num, i in enumerate(range(0, len(records), self.batch_size), 1):
            batch = records[i:i + self.batch_size]
            
            # Log de progreso cada 5 lotes o en el último
            if batch_num % 5 == 0 or batch_num == total_batches:
                logger.info(f"[FactLoader] Lote {batch_num}/{total_batches} - {inserted} insertados hasta ahora")
            
            try:
                response = self.client.client.table("fact_regalias")\
                    .insert(batch)\
                    .execute()
                
                if response.data:
                    inserted += len(response.data)
                    
            except Exception as e:
                error_msg = str(e)
                
                # Si es error de duplicado, intentar uno por uno
                if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
                    logger.debug(f"[FactLoader] Lote {batch_num} tiene duplicados, procesando individualmente")
                    
                    for record in batch:
                        try:
                            self.client.client.table("fact_regalias")\
                                .insert(record)\
                                .execute()
                            inserted += 1
                        except Exception as e2:
                            if "duplicate" not in str(e2).lower():
                                errors += 1
                                error_details.append({
                                    "batch": batch_num,
                                    "error": str(e2),
                                    "record_campo_id": record.get("campo_id")
                                })
                else:
                    errors += len(batch)
                    error_details.append({
                        "batch": batch_num,
                        "error": error_msg,
                        "batch_size": len(batch)
                    })
                    logger.error(f"[FactLoader] Error en lote {batch_num}: {e}")
        
        return {
            "inserted": inserted,
            "errors": errors,
            "error_details": error_details
        }
    
    def _result(self, status: str, message: str = None) -> Dict[str, Any]:
        """Construye resultado con estadísticas."""
        result = {
            "status": status,
            "stats": self.stats.copy()
        }
        if message:
            result["message"] = message
        return result
    
    def reset_stats(self) -> None:
        """Resetea estadísticas."""
        self.stats = {
            "total_processed": 0,
            "inserted": 0,
            "skipped_no_tiempo": 0,
            "skipped_no_campo": 0,
            "errors": 0,
        }


def load_regalias(
    records: List[Dict[str, Any]], 
    source_id: str = "api_regalias",
    batch_size: int = 500
) -> Dict[str, Any]:
    """
    Función de conveniencia para cargar registros de regalías.
    
    Args:
        records: Lista de registros transformados
        source_id: ID de la fuente
        batch_size: Tamaño de lote
        
    Returns:
        Estadísticas de la carga
    """
    loader = FactLoader(batch_size=batch_size)
    return loader.load(records, source_id)
