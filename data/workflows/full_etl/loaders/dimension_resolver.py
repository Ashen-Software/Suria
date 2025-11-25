"""
Resolver de dimensiones para lookups y upserts.

Gestiona:
- dim_tiempo: Lookup por fecha (ya poblada por seed)
- dim_territorios: Lookup por departamento+municipio (ya poblada por seed)
- dim_campos: Upsert por nombre_campo (se crea si no existe)

Incluye cache en memoria para evitar queries repetidas.
"""
from typing import Dict, Any, Optional, Tuple
from datetime import date
from functools import lru_cache
import unicodedata

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from services.backend_client import BackendClient
from logs_config.logger import app_logger as logger


def remove_accents(text: str) -> str:
    """
    Remueve tildes y acentos de un texto.
    
    Ej: "Santandér" -> "Santander", "Araúca" -> "Arauca"
    """
    if not text:
        return text
    # NFD descompone caracteres (á -> a + ́), luego filtramos los acentos
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')


class DimensionResolver:
    """
    Resuelve FKs de dimensiones para inserción en fact tables.
    
    Usa cache en memoria para minimizar queries a la DB.
    """
    
    def __init__(self, client: Optional[BackendClient] = None):
        """
        Inicializa el resolver.
        
        Args:
            client: BackendClient opcional. Si None, crea uno nuevo.
        """
        self.client = client or BackendClient()
        
        # Caches en memoria
        self._tiempo_cache: Dict[date, int] = {}
        self._territorio_cache: Dict[Tuple[str, str], int] = {}  # Cache normalizado (sin tildes)
        self._territorio_full_cache: Dict[Tuple[str, str], int] = {}  # Cache con nombres originales
        self._campo_cache: Dict[str, int] = {}
        
        # Tracking de campos creados (para resumen)
        self._campos_created_ids: list = []
        
        # Estadísticas
        self.stats = {
            "tiempo_lookups": 0,
            "tiempo_cache_hits": 0,
            "territorio_lookups": 0,
            "territorio_cache_hits": 0,
            "campo_lookups": 0,
            "campo_cache_hits": 0,
            "campo_inserts": 0,
        }
    
    def resolve_tiempo_id(self, fecha: date) -> Optional[int]:
        """
        Obtiene el ID de dim_tiempo para una fecha.
        
        Args:
            fecha: Fecha (primer día del mes)
            
        Returns:
            ID de la dimensión, o None si no existe
        """
        # Normalizar a primer día del mes
        if isinstance(fecha, str):
            from datetime import datetime
            fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
        
        fecha_normalizada = date(fecha.year, fecha.month, 1)
        
        # Verificar cache
        if fecha_normalizada in self._tiempo_cache:
            self.stats["tiempo_cache_hits"] += 1
            return self._tiempo_cache[fecha_normalizada]
        
        self.stats["tiempo_lookups"] += 1
        
        if not self.client.client:
            logger.warning("[DimensionResolver] Cliente no disponible para lookup tiempo")
            return None
        
        try:
            response = self.client.client.table("dim_tiempo")\
                .select("id")\
                .eq("fecha", fecha_normalizada.isoformat())\
                .limit(1)\
                .execute()
            
            if response.data and len(response.data) > 0:
                tiempo_id = response.data[0]["id"]
                self._tiempo_cache[fecha_normalizada] = tiempo_id
                return tiempo_id
            else:
                logger.warning(f"[DimensionResolver] Fecha no encontrada en dim_tiempo: {fecha_normalizada}")
                return None
                
        except Exception as e:
            logger.error(f"[DimensionResolver] Error buscando tiempo {fecha_normalizada}: {e}")
            return None
    
    def resolve_territorio_id(
        self, 
        departamento: str, 
        municipio: str
    ) -> Optional[int]:
        """
        Obtiene el ID de dim_territorios para un departamento+municipio.
        
        Normaliza tildes para matching flexible.
        
        Args:
            departamento: Nombre del departamento
            municipio: Nombre del municipio
            
        Returns:
            ID de la dimensión, o None si no existe
        """
        # Normalizar: quitar tildes, espacios, mayúsculas
        departamento_norm = remove_accents((departamento or "").strip()).upper()
        municipio_norm = remove_accents((municipio or "").strip()).upper()
        
        if not departamento_norm or not municipio_norm:
            return None
        
        cache_key = (departamento_norm, municipio_norm)
        
        # Verificar cache
        if cache_key in self._territorio_cache:
            self.stats["territorio_cache_hits"] += 1
            return self._territorio_cache[cache_key]
        
        self.stats["territorio_lookups"] += 1
        
        if not self.client.client:
            logger.warning("[DimensionResolver] Cliente no disponible para lookup territorio")
            return None
        
        try:
            # Buscar comparando sin tildes usando cache precargado
            # Si el cache está poblado, buscar ahí (más eficiente)
            if self._territorio_full_cache:
                for (depto_db, muni_db), tid in self._territorio_full_cache.items():
                    depto_db_norm = remove_accents(depto_db).upper()
                    muni_db_norm = remove_accents(muni_db).upper()
                    if depto_db_norm == departamento_norm and muni_db_norm == municipio_norm:
                        self._territorio_cache[cache_key] = tid
                        return tid
                logger.debug(f"[DimensionResolver] Territorio no encontrado en cache: {departamento_norm}/{municipio_norm}")
                return None
            
            # Si no hay cache completo, buscar en DB
            # Usamos ilike con el valor original (puede fallar con tildes)
            response = self.client.client.table("dim_territorios")\
                .select("id, departamento, municipio")\
                .execute()
            
            if response.data:
                for row in response.data:
                    depto_db_norm = remove_accents(row["departamento"]).upper()
                    muni_db_norm = remove_accents(row["municipio"]).upper()
                    if depto_db_norm == departamento_norm and muni_db_norm == municipio_norm:
                        territorio_id = row["id"]
                        self._territorio_cache[cache_key] = territorio_id
                        return territorio_id
            
            logger.debug(f"[DimensionResolver] Territorio no encontrado: {departamento_norm}/{municipio_norm}")
            return None
                
        except Exception as e:
            logger.error(f"[DimensionResolver] Error buscando territorio {departamento_norm}/{municipio_norm}: {e}")
            return None
    
    def resolve_or_create_campo_id(
        self,
        nombre_campo: str,
        contrato: Optional[str] = None,
        territorio_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Obtiene o crea el ID de dim_campos para un campo.
        
        Si el campo no existe, lo crea con los datos proporcionados.
        
        Args:
            nombre_campo: Nombre del campo (clave única)
            contrato: Código del contrato (opcional)
            territorio_id: FK a dim_territorios (opcional)
            
        Returns:
            ID de la dimensión
        """
        # Normalizar
        nombre_campo = (nombre_campo or "").strip().upper()
        
        if not nombre_campo:
            logger.warning("[DimensionResolver] nombre_campo vacío")
            return None
        
        # Verificar cache
        if nombre_campo in self._campo_cache:
            self.stats["campo_cache_hits"] += 1
            return self._campo_cache[nombre_campo]
        
        self.stats["campo_lookups"] += 1
        
        if not self.client.client:
            logger.warning("[DimensionResolver] Cliente no disponible para lookup/create campo")
            return None
        
        try:
            # Primero intentar lookup
            response = self.client.client.table("dim_campos")\
                .select("id")\
                .eq("nombre_campo", nombre_campo)\
                .limit(1)\
                .execute()
            
            if response.data and len(response.data) > 0:
                campo_id = response.data[0]["id"]
                self._campo_cache[nombre_campo] = campo_id
                return campo_id
            
            # No existe, crear
            self.stats["campo_inserts"] += 1
            
            new_campo = {
                "nombre_campo": nombre_campo,
                "activo": True
            }
            
            if contrato:
                new_campo["contrato"] = contrato.strip()
            
            if territorio_id:
                new_campo["territorio_id"] = territorio_id
            
            insert_response = self.client.client.table("dim_campos")\
                .insert(new_campo)\
                .execute()
            
            if insert_response.data and len(insert_response.data) > 0:
                campo_id = insert_response.data[0]["id"]
                self._campo_cache[nombre_campo] = campo_id
                self._campos_created_ids.append(campo_id)  # Trackear para resumen
                return campo_id
            else:
                logger.error(f"[DimensionResolver] No se pudo crear campo: {nombre_campo}")
                return None
                
        except Exception as e:
            # Si es error de duplicado (race condition), intentar lookup de nuevo
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                try:
                    response = self.client.client.table("dim_campos")\
                        .select("id")\
                        .eq("nombre_campo", nombre_campo)\
                        .limit(1)\
                        .execute()
                    
                    if response.data and len(response.data) > 0:
                        campo_id = response.data[0]["id"]
                        self._campo_cache[nombre_campo] = campo_id
                        return campo_id
                except:
                    pass
            
            logger.error(f"[DimensionResolver] Error creando campo {nombre_campo}: {e}")
            return None
    
    def resolve_all_for_record(self, record: Dict[str, Any]) -> Dict[str, Optional[int]]:
        """
        Resuelve todas las FKs necesarias para un registro de regalías.
        
        Args:
            record: Registro transformado (con structure {"data": {...}, "dimensions": {...}})
            
        Returns:
            Dict con FKs resueltas:
            {
                "tiempo_id": int | None,
                "campo_id": int | None,
                "territorio_id": int | None  # Para referencia, no se usa en fact
            }
        """
        data = record.get("data", {})
        dimensions = record.get("dimensions", {})
        
        # 1. Resolver tiempo
        tiempo_data = dimensions.get("tiempo", {})
        fecha = tiempo_data.get("fecha") or data.get("tiempo_fecha")
        tiempo_id = self.resolve_tiempo_id(fecha) if fecha else None
        
        # 2. Resolver territorio (para campo)
        territorio_data = dimensions.get("territorio", {})
        departamento = territorio_data.get("departamento") or data.get("departamento")
        municipio = territorio_data.get("municipio") or data.get("municipio")
        territorio_id = self.resolve_territorio_id(departamento, municipio) if departamento and municipio else None
        
        # 3. Resolver o crear campo
        campo_data = dimensions.get("campo", {})
        nombre_campo = campo_data.get("nombre_campo") or data.get("campo_nombre")
        contrato = campo_data.get("contrato") or data.get("contrato")
        campo_id = self.resolve_or_create_campo_id(nombre_campo, contrato, territorio_id) if nombre_campo else None
        
        return {
            "tiempo_id": tiempo_id,
            "campo_id": campo_id,
            "territorio_id": territorio_id
        }
    
    def preload_tiempo_cache(self, start_year: int = 2010, end_year: int = 2036) -> int:
        """
        Pre-carga el cache de tiempo para un rango de años.
        
        Útil para evitar múltiples queries al procesar muchos registros.
        
        Returns:
            Número de registros cargados en cache
        """
        if not self.client.client:
            return 0
        
        try:
            start_date = f"{start_year}-01-01"
            end_date = f"{end_year}-12-01"
            
            response = self.client.client.table("dim_tiempo")\
                .select("id, fecha")\
                .gte("fecha", start_date)\
                .lte("fecha", end_date)\
                .execute()
            
            if response.data:
                for row in response.data:
                    from datetime import datetime
                    fecha = datetime.strptime(row["fecha"], "%Y-%m-%d").date()
                    self._tiempo_cache[fecha] = row["id"]
                
                logger.info(f"[DimensionResolver] Pre-cargados {len(response.data)} registros de tiempo en cache")
                return len(response.data)
                
        except Exception as e:
            logger.error(f"[DimensionResolver] Error pre-cargando cache de tiempo: {e}")
        
        return 0
    
    def preload_territorio_cache(self) -> int:
        """
        Pre-carga el cache de territorios con normalización de tildes.
        
        Returns:
            Número de registros cargados en cache
        """
        if not self.client.client:
            return 0
        
        try:
            response = self.client.client.table("dim_territorios")\
                .select("id, departamento, municipio")\
                .execute()
            
            if response.data:
                for row in response.data:
                    # Cache con nombres originales (para búsqueda interna)
                    orig_key = (row["departamento"], row["municipio"])
                    self._territorio_full_cache[orig_key] = row["id"]
                    
                    # Cache normalizado (sin tildes, mayúsculas)
                    norm_key = (
                        remove_accents(row["departamento"]).upper(),
                        remove_accents(row["municipio"]).upper()
                    )
                    self._territorio_cache[norm_key] = row["id"]
                
                logger.info(f"[DimensionResolver] Pre-cargados {len(response.data)} registros de territorio en cache (normalizados)")
                return len(response.data)
                
        except Exception as e:
            logger.error(f"[DimensionResolver] Error pre-cargando cache de territorios: {e}")
        
        return 0
    
    def preload_campo_cache(self) -> int:
        """
        Pre-carga el cache de campos existentes.
        
        Returns:
            Número de registros cargados en cache
        """
        if not self.client.client:
            return 0
        
        try:
            response = self.client.client.table("dim_campos")\
                .select("id, nombre_campo")\
                .execute()
            
            if response.data:
                for row in response.data:
                    self._campo_cache[row["nombre_campo"].upper()] = row["id"]
                
                logger.info(f"[DimensionResolver] Pre-cargados {len(response.data)} registros de campo en cache")
                return len(response.data)
                
        except Exception as e:
            logger.error(f"[DimensionResolver] Error pre-cargando cache de campos: {e}")
        
        return 0
    
    def preload_all_caches(self) -> Dict[str, int]:
        """
        Pre-carga todos los caches de dimensiones.
        
        Returns:
            Dict con número de registros cargados por dimensión
        """
        return {
            "tiempo": self.preload_tiempo_cache(),
            "territorios": self.preload_territorio_cache(),
            "campos": self.preload_campo_cache()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso del resolver."""
        return {
            **self.stats,
            "cache_sizes": {
                "tiempo": len(self._tiempo_cache),
                "territorio": len(self._territorio_cache),
                "territorio_full": len(self._territorio_full_cache),
                "campo": len(self._campo_cache)
            },
            "campos_created_range": self._get_campos_created_summary()
        }
    
    def _get_campos_created_summary(self) -> str:
        """Retorna resumen de IDs de campos creados."""
        if not self._campos_created_ids:
            return "ninguno"
        
        ids = sorted(self._campos_created_ids)
        if len(ids) == 1:
            return f"ID {ids[0]}"
        return f"IDs {ids[0]} - {ids[-1]} ({len(ids)} campos)"
    
    def log_campos_created_summary(self) -> None:
        """Loguea resumen de campos creados (llamar al final del proceso)."""
        if self._campos_created_ids:
            summary = self._get_campos_created_summary()
            logger.info(f"[DimensionResolver] Campos creados: {summary}")
    
    def clear_caches(self) -> None:
        """Limpia todos los caches."""
        self._tiempo_cache.clear()
        self._territorio_cache.clear()
        self._territorio_full_cache.clear()
        self._campo_cache.clear()
        self._campos_created_ids.clear()
        logger.debug("[DimensionResolver] Caches limpiados")
