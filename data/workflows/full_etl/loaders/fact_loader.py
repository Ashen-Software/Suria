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
    Usa UPSERT para evitar duplicados cuando se re-ejecuta el ETL.
    
    DISEÑO GENÉRICO:
    - El transformer produce records con estructura {"fact_table": str, "data": dict, "dimensions": dict}
    - El loader es agnóstico a la fuente: lee fact_table del record
    - Solo necesita conocer las unique_columns por tabla para el UPSERT
    """
    
    # UNIQUE columns por fact_table
    # Necesario para el ON CONFLICT del UPSERT
    UNIQUE_COLUMNS_BY_TABLE = {
        "fact_regalias": "tiempo_id,campo_id,tipo_hidrocarburo",
        "fact_demanda_gas": "tiempo_id,territorio_id,escenario",
        # Agregar
    }
    
    # Columnas numericas que requieren conversion a float (en todas las tablas)
    NUMERIC_COLUMNS = {
        "precio_usd", "porcentaje_regalia", "produccion_gravable",
        "volumen_regalia", "valor_regalias_cop", "demanda_gbtud",
        "latitud", "longitud"
    }
    
    def __init__(
        self, 
        client: Optional[BackendClient] = None,
        dimension_resolver: Optional[DimensionResolver] = None,
        batch_size: int = 5000
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
            "duplicates_in_batch": 0,
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
        
        # Deduplicar registros antes del UPSERT
        if fact_records:
            fact_records, duplicates_removed = self._deduplicate_records(fact_records)
            if duplicates_removed > 0:
                logger.info(f"[FactLoader] Removidos {duplicates_removed} registros duplicados. Quedan {len(fact_records)} únicos.")
                self.stats["duplicates_in_batch"] = duplicates_removed
        
        # UPSERT en lotes
        if fact_records:
            upsert_result = self._batch_upsert(fact_records, source_id)
            self.stats["inserted"] = upsert_result.get("upserted", 0)
            self.stats["errors"] += upsert_result.get("errors", 0)
            error_details.extend(upsert_result.get("error_details", []))
        
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
            f"[FactLoader] Carga completada: {self.stats['inserted']} upserted, "
            f"{self.stats.get('duplicates_in_batch', 0)} duplicados removidos, "
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
        Prepara un registro para inserción en su fact_table correspondiente.
        
        GENÉRICO: Lee la estructura del transformer sin mapeos hardcodeados.
        El transformer ya produjo {"fact_table": str, "data": dict, "dimensions": dict}
        
        Resuelve FKs y construye el registro final.
        
        Returns:
            Dict listo para UPSERT, o None si faltan FKs críticas
        """
        # Resolver FKs desde dimensions
        fks = self.resolver.resolve_all_for_record(record)
        
        # Obtener fact_table del record (definido por transformer)
        fact_table = record.get("fact_table", "fact_regalias")
        
        # Validar FKs críticas (tiempo es siempre requerido)
        if fks["tiempo_id"] is None:
            self.stats["skipped_no_tiempo"] += 1
            data = record.get("data", {})
            logger.debug(
                f"[FactLoader] Registro omitido por falta de tiempo_id. "
                f"Fecha: {data.get('tiempo_fecha')}"
            )
            return None
        
        # campo_id es crítico para fact_regalias
        if fact_table == "fact_regalias" and fks["campo_id"] is None:
            self.stats["skipped_no_campo"] += 1
            data = record.get("data", {})
            logger.debug(
                f"[FactLoader] Registro omitido por falta de campo_id. "
                f"Campo: {data.get('campo_nombre')}"
            )
            return None
        
        # Construir registro base con FKs y metadata
        fact_record = {
            "tiempo_id": fks["tiempo_id"],
            "source_id": source_id,
        }
        
        # Agregar campo_id si existe
        if fks.get("campo_id"):
            fact_record["campo_id"] = fks["campo_id"]
        
        # Agregar territorio_id si existe y la tabla lo necesita
        if fks.get("territorio_id"):
            fact_record["territorio_id"] = fks["territorio_id"]
        
        # Copiar TODOS los campos de data (ya vienen mapeados del transformer)
        data = record.get("data", {})
        for col, value in data.items():
            # Saltar campos que ya procesamos o son para dimensiones
            if col in ["tiempo_fecha", "campo_nombre", "departamento", "municipio", 
                       "latitud", "longitud", "contrato"]:
                continue
            
            if value is not None:
                # Convertir a float si es columna numérica
                if col in self.NUMERIC_COLUMNS:
                    try:
                        value = float(value) if value != "" else None
                    except (ValueError, TypeError):
                        value = None
                
                # Sanitizar NaN/Inf
                value = sanitize_value(value)
                
                if value is not None:
                    fact_record[col] = value
        
        # Guardar fact_table para uso en batch_upsert
        fact_record["_fact_table"] = fact_table
        
        return fact_record
    
    def _deduplicate_records(
        self, 
        records: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Elimina registros duplicados basándose en la clave única por tabla.
        
        PostgreSQL no permite que un UPSERT afecte la misma fila dos veces
        en un solo comando, así que debemos deduplicar antes de enviar.
        
        GENÉRICO: Usa UNIQUE_COLUMNS_BY_TABLE para determinar la clave.
        Mantiene el ÚLTIMO registro para cada clave (asumiendo datos más recientes).
        
        Returns:
            Tupla (registros_únicos, cantidad_duplicados_removidos)
        """
        seen = {}
        
        for record in records:
            # Obtener la tabla y sus columnas únicas
            fact_table = record.get("_fact_table", "fact_regalias")
            unique_cols_str = self.UNIQUE_COLUMNS_BY_TABLE.get(fact_table, "tiempo_id")
            unique_cols = unique_cols_str.split(",")
            
            # Construir clave dinámica basada en las columnas únicas
            key = tuple([fact_table] + [record.get(col) for col in unique_cols])
            
            # Sobrescribe si ya existe (mantiene el último)
            seen[key] = record
        
        unique_records = list(seen.values())
        duplicates_removed = len(records) - len(unique_records)
        
        return unique_records, duplicates_removed
    
    def _batch_upsert(
        self, 
        records: List[Dict[str, Any]], 
        source_id: str
    ) -> Dict[str, Any]:
        """
        Upsert de registros en lotes.
        
        UPSERT = INSERT si no existe, UPDATE si ya existe.
        Evita duplicados cuando se re-ejecuta el ETL con datos actualizados.
        
        GENÉRICO: Agrupa por fact_table y usa unique_columns correspondientes.
        
        Returns:
            Dict con estadísticas de upsert
        """
        if not self.client.client:
            logger.error("[FactLoader] Cliente no disponible para upsert")
            return {"upserted": 0, "errors": len(records), "error_details": []}
        
        # Agrupar registros por fact_table
        records_by_table: Dict[str, List[Dict]] = {}
        for record in records:
            fact_table = record.pop("_fact_table", "fact_regalias")
            if fact_table not in records_by_table:
                records_by_table[fact_table] = []
            records_by_table[fact_table].append(record)
        
        upserted = 0
        errors = 0
        error_details = []
        
        # Procesar cada tabla
        for fact_table, table_records in records_by_table.items():
            unique_columns = self.UNIQUE_COLUMNS_BY_TABLE.get(fact_table)
            
            if not unique_columns:
                logger.warning(f"[FactLoader] No hay unique_columns definidas para {fact_table}, saltando...")
                continue
            
            total_batches = (len(table_records) + self.batch_size - 1) // self.batch_size
            logger.info(f"[FactLoader] Upsert en {fact_table}: {len(table_records)} registros en {total_batches} lotes")
            
            for batch_num, i in enumerate(range(0, len(table_records), self.batch_size), 1):
                batch = table_records[i:i + self.batch_size]
                
                # Log de progreso cada 5 lotes o en el último
                if batch_num % 5 == 0 or batch_num == total_batches:
                    logger.info(f"[FactLoader] {fact_table} lote {batch_num}/{total_batches} - {upserted} procesados")
                
                try:
                    response = self.client.client.table(fact_table)\
                        .upsert(batch, on_conflict=unique_columns)\
                        .execute()
                    
                    if response.data:
                        upserted += len(response.data)
                        
                except Exception as e:
                    # Si falla el batch, intentar uno por uno
                    logger.warning(f"[FactLoader] Error en lote {batch_num} de {fact_table}, procesando individualmente: {e}")
                    
                    for record in batch:
                        try:
                            self.client.client.table(fact_table)\
                                .upsert(record, on_conflict=unique_columns)\
                                .execute()
                            upserted += 1
                        except Exception as e2:
                            errors += 1
                            error_details.append({
                                "table": fact_table,
                                "batch": batch_num,
                                "error": str(e2),
                                "record_tiempo_id": record.get("tiempo_id")
                            })
        
        return {
            "upserted": upserted,
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
