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
    
    Dimensiones soportadas:
    - dim_tiempo: Lookup por fecha
    - dim_territorios: Lookup por departamento+municipio
    - dim_campos: Upsert por nombre_campo
    - dim_resoluciones: Upsert por numero_resolucion (MinMinas)
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
        self._campo_cache: Dict[str, int] = {}
        self._resolucion_cache: Dict[str, int] = {}  # numero_resolucion -> id
        
        # Tracking de campos creados (para resumen)
        self._campos_created_ids: list = []
        self._resoluciones_created_ids: list = []
        
        # Tracking de territorios no encontrados (para resumen)
        self._territorios_not_found: set = set()
        
        # Estadísticas
        self.stats = {
            "tiempo_lookups": 0,
            "tiempo_cache_hits": 0,
            "territorio_lookups": 0,
            "territorio_cache_hits": 0,
            "campo_lookups": 0,
            "campo_cache_hits": 0,
            "campo_inserts": 0,
            "resolucion_lookups": 0,
            "resolucion_cache_hits": 0,
            "resolucion_inserts": 0,
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
        
        # Verificar cache normalizado (pre-cargado por preload_territorio_cache)
        if cache_key in self._territorio_cache:
            self.stats["territorio_cache_hits"] += 1
            return self._territorio_cache[cache_key]
        
        self.stats["territorio_lookups"] += 1
        
        # Si el cache fue pre-cargado y no está, no existe
        if self._territorio_cache:
            # Trackear para resumen al final (solo únicos)
            self._territorios_not_found.add(cache_key)
            return None
        
        # Fallback: Si cache no fue pre-cargado, buscar en DB
        if not self.client.client:
            return None
        
        try:
            response = self.client.client.table("dim_territorios")\
                .select("id, departamento, municipio")\
                .execute()
            
            if response.data:
                # Poblar cache mientras buscamos
                for row in response.data:
                    norm_key = (
                        remove_accents(row["departamento"]).upper(),
                        remove_accents(row["municipio"]).upper()
                    )
                    self._territorio_cache[norm_key] = row["id"]
                
                # Buscar ahora en cache poblado
                if cache_key in self._territorio_cache:
                    return self._territorio_cache[cache_key]
            
            return None
                
        except Exception as e:
            logger.error(f"[DimensionResolver] Error buscando territorio {departamento_norm}/{municipio_norm}: {e}")
            return None
    
    def resolve_or_create_campo_id(
        self,
        nombre_campo: str,
        contrato: Optional[str] = None,
        territorio_id: Optional[int] = None,
        operador: Optional[str] = None
    ) -> Optional[int]:
        """
        Obtiene o crea el ID de dim_campos para un campo.
        
        Si el campo no existe, lo crea con los datos proporcionados.
        territorio_id es opcional: si no se resuelve (ej: "NN"), se omite.
        
        Args:
            nombre_campo: Nombre del campo (clave única)
            contrato: Código del contrato (opcional)
            territorio_id: FK a dim_territorios (opcional)
            operador: Nombre del operador del campo (opcional)
            
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
            # Construir datos del campo (solo campos con valor)
            campo_data = {
                "nombre_campo": nombre_campo,
                "activo": True
            }
            
            if contrato:
                campo_data["contrato"] = contrato.strip()
            
            if operador:
                campo_data["operador"] = operador.strip()
            
            # Esto evita errores de FK cuando el territorio no existe (ej: "NN")
            if territorio_id is not None:
                campo_data["territorio_id"] = territorio_id
            
            # UPSERT: INSERT si no existe, UPDATE si ya existe
            # on_conflict="nombre_campo" indica la columna UNIQUE para detectar conflicto
            upsert_response = self.client.client.table("dim_campos")\
                .upsert(campo_data, on_conflict="nombre_campo")\
                .execute()
            
            if upsert_response.data and len(upsert_response.data) > 0:
                campo_id = upsert_response.data[0]["id"]
                
                # Si es nuevo (no estaba en cache), trackear
                if nombre_campo not in self._campo_cache:
                    self.stats["campo_inserts"] += 1
                    self._campos_created_ids.append(campo_id)
                
                self._campo_cache[nombre_campo] = campo_id
                return campo_id
            else:
                logger.error(f"[DimensionResolver] No se pudo upsert campo: {nombre_campo}")
                return None
                
        except Exception as e:
            # Fallback: si falla el upsert, intentar lookup simple
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
        Resuelve todas las FKs necesarias para un registro.
        
        Soporta:
        - fact_regalias: tiempo, territorio, campo
        - fact_oferta_gas: tiempo, campo, resolucion
        - fact_demanda_gas: tiempo, territorio
        
        Args:
            record: Registro transformado (con structure {"data": {...}, "dimensions": {...}})
            
        Returns:
            Dict con FKs resueltas:
            {
                "tiempo_id": int | None,
                "campo_id": int | None,
                "territorio_id": int | None,
                "resolucion_id": int | None
            }
        """
        data = record.get("data", {})
        dimensions = record.get("dimensions", {})
        fact_table = record.get("fact_table", "")
        
        # 1. Resolver tiempo (siempre requerido)
        tiempo_data = dimensions.get("tiempo", {})
        fecha = tiempo_data.get("fecha") or data.get("tiempo_fecha")
        tiempo_id = self.resolve_tiempo_id(fecha) if fecha else None
        
        # 2. Resolver territorio (para regalias y demanda)
        territorio_id = None
        if fact_table in ["fact_regalias", "fact_demanda_gas"]:
            territorio_data = dimensions.get("territorio", {})
            departamento = territorio_data.get("departamento") or data.get("departamento")
            municipio = territorio_data.get("municipio") or data.get("municipio")
            territorio_id = self.resolve_territorio_id(departamento, municipio) if departamento and municipio else None
        
        # 3. Resolver o crear campo (para regalias y oferta)
        campo_id = None
        if fact_table in ["fact_regalias", "fact_oferta_gas"]:
            campo_data = dimensions.get("campo", {})
            nombre_campo = campo_data.get("nombre_campo") or data.get("campo_nombre")
            contrato = campo_data.get("contrato") or data.get("contrato")
            operador = campo_data.get("operador") or data.get("operador")
            campo_id = self.resolve_or_create_campo_id(
                nombre_campo, contrato, territorio_id, operador
            ) if nombre_campo else None
        
        # 4. Resolver o crear resolución (para oferta)
        resolucion_id = None
        if fact_table == "fact_oferta_gas":
            resolucion_data = dimensions.get("resolucion", {})
            numero_resolucion = resolucion_data.get("numero_resolucion") or data.get("resolucion_number")
            if numero_resolucion:
                # Extraer metadata de resolución si está disponible
                periodo_desde = resolucion_data.get("periodo_desde")
                periodo_hasta = resolucion_data.get("periodo_hasta")
                url_pdf = resolucion_data.get("url_pdf")
                
                resolucion_id = self.resolve_or_create_resolucion_id(
                    numero_resolucion=numero_resolucion,
                    periodo_desde=periodo_desde,
                    periodo_hasta=periodo_hasta,
                    url_pdf=url_pdf,
                    source_id=data.get("source_id")
                )
        
        return {
            "tiempo_id": tiempo_id,
            "campo_id": campo_id,
            "territorio_id": territorio_id,
            "resolucion_id": resolucion_id
        }
    
    def resolve_or_create_resolucion_id(
        self,
        numero_resolucion: str,
        periodo_desde: Optional[date] = None,
        periodo_hasta: Optional[date] = None,
        url_pdf: Optional[str] = None,
        url_soporte_magnetico: Optional[str] = None,
        titulo: Optional[str] = None,
        source_id: Optional[str] = None
    ) -> Optional[int]:
        """
        Obtiene o crea el ID de dim_resoluciones para una resolución.
        
        Las resoluciones de MinMinas definen períodos de declaración de producción.
        Si la resolución no existe, la crea con los datos proporcionados.
        
        Args:
            numero_resolucion: Número de resolución (clave única)
            periodo_desde: Fecha inicio del período de la resolución
            periodo_hasta: Fecha fin del período de la resolución
            url_pdf: URL del PDF de la resolución
            url_soporte_magnetico: URL del Excel de soporte
            titulo: Título de la resolución
            source_id: ID de la fuente ETL
            
        Returns:
            ID de la dimensión, o None si falla
        """
        # Normalizar
        numero_resolucion = (numero_resolucion or "").strip()
        
        if not numero_resolucion:
            logger.warning("[DimensionResolver] numero_resolucion vacío")
            return None
        
        # Verificar cache
        if numero_resolucion in self._resolucion_cache:
            self.stats["resolucion_cache_hits"] += 1
            return self._resolucion_cache[numero_resolucion]
        
        self.stats["resolucion_lookups"] += 1
        
        if not self.client.client:
            logger.warning("[DimensionResolver] Cliente no disponible para lookup/create resolución")
            return None
        
        try:
            # Construir datos de la resolución
            resolucion_data = {
                "numero_resolucion": numero_resolucion,
            }
            
            # Agregar campos opcionales si tienen valor
            if periodo_desde:
                if isinstance(periodo_desde, str):
                    resolucion_data["periodo_desde"] = periodo_desde
                else:
                    resolucion_data["periodo_desde"] = periodo_desde.isoformat()
            else:
                # Período por defecto si no se proporciona (requerido en BD)
                resolucion_data["periodo_desde"] = "2020-01-01"
            
            if periodo_hasta:
                if isinstance(periodo_hasta, str):
                    resolucion_data["periodo_hasta"] = periodo_hasta
                else:
                    resolucion_data["periodo_hasta"] = periodo_hasta.isoformat()
            else:
                resolucion_data["periodo_hasta"] = "2030-12-31"
            
            if url_pdf:
                resolucion_data["url_pdf"] = url_pdf
            
            if url_soporte_magnetico:
                resolucion_data["url_soporte_magnetico"] = url_soporte_magnetico
            
            if titulo:
                resolucion_data["titulo"] = titulo
            
            if source_id:
                resolucion_data["source_id"] = source_id
            
            # UPSERT: INSERT si no existe, UPDATE si ya existe
            upsert_response = self.client.client.table("dim_resoluciones")\
                .upsert(resolucion_data, on_conflict="numero_resolucion")\
                .execute()
            
            if upsert_response.data and len(upsert_response.data) > 0:
                resolucion_id = upsert_response.data[0]["id"]
                
                # Si es nuevo (no estaba en cache), trackear
                if numero_resolucion not in self._resolucion_cache:
                    self.stats["resolucion_inserts"] += 1
                    self._resoluciones_created_ids.append(resolucion_id)
                
                self._resolucion_cache[numero_resolucion] = resolucion_id
                return resolucion_id
            else:
                logger.error(f"[DimensionResolver] No se pudo upsert resolución: {numero_resolucion}")
                return None
                
        except Exception as e:
            # Fallback: si falla el upsert, intentar lookup simple
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                try:
                    response = self.client.client.table("dim_resoluciones")\
                        .select("id")\
                        .eq("numero_resolucion", numero_resolucion)\
                        .limit(1)\
                        .execute()
                    
                    if response.data and len(response.data) > 0:
                        resolucion_id = response.data[0]["id"]
                        self._resolucion_cache[numero_resolucion] = resolucion_id
                        return resolucion_id
                except:
                    pass
            
            logger.error(f"[DimensionResolver] Error creando resolución {numero_resolucion}: {e}")
            return None
    
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
                    # Cache normalizado (sin tildes, mayúsculas) - O(1) lookup
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
            "campos": self.preload_campo_cache(),
            "resoluciones": self.preload_resolucion_cache()
        }
    
    def preload_resolucion_cache(self) -> int:
        """
        Pre-carga el cache de resoluciones existentes.
        
        Returns:
            Número de registros cargados en cache
        """
        if not self.client.client:
            return 0
        
        try:
            response = self.client.client.table("dim_resoluciones")\
                .select("id, numero_resolucion")\
                .execute()
            
            if response.data:
                for row in response.data:
                    self._resolucion_cache[row["numero_resolucion"]] = row["id"]
                
                logger.info(f"[DimensionResolver] Pre-cargados {len(response.data)} registros de resolución en cache")
                return len(response.data)
                
        except Exception as e:
            logger.error(f"[DimensionResolver] Error pre-cargando cache de resoluciones: {e}")
        
        return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso del resolver."""
        return {
            **self.stats,
            "cache_sizes": {
                "tiempo": len(self._tiempo_cache),
                "territorio": len(self._territorio_cache),
                "campo": len(self._campo_cache),
                "resolucion": len(self._resolucion_cache)
            },
            "campos_created_range": self._get_campos_created_summary(),
            "resoluciones_created_range": self._get_resoluciones_created_summary(),
            "territorios_not_found": len(self._territorios_not_found)
        }
    
    def _get_campos_created_summary(self) -> str:
        """Retorna resumen de IDs de campos creados."""
        if not self._campos_created_ids:
            return "ninguno"
        
        ids = sorted(self._campos_created_ids)
        if len(ids) == 1:
            return f"ID {ids[0]}"
        return f"IDs {ids[0]} - {ids[-1]} ({len(ids)} campos)"
    
    def _get_resoluciones_created_summary(self) -> str:
        """Retorna resumen de IDs de resoluciones creadas."""
        if not self._resoluciones_created_ids:
            return "ninguno"
        
        ids = sorted(self._resoluciones_created_ids)
        if len(ids) == 1:
            return f"ID {ids[0]}"
        return f"IDs {ids[0]} - {ids[-1]} ({len(ids)} resoluciones)"
    
    def log_summary(self) -> None:
        """Loguea resumen de operaciones (llamar al final del proceso)."""
        # Campos creados
        if self._campos_created_ids:
            summary = self._get_campos_created_summary()
            logger.info(f"[DimensionResolver] Campos creados: {summary}")
        
        # Resoluciones creadas
        if self._resoluciones_created_ids:
            summary = self._get_resoluciones_created_summary()
            logger.info(f"[DimensionResolver] Resoluciones creadas: {summary}")
        
        # Territorios no encontrados
        if self._territorios_not_found:
            count = len(self._territorios_not_found)
            # Mostrar solo primeros 5 ejemplos si hay muchos
            examples = list(self._territorios_not_found)[:5]
            examples_str = ", ".join(f"{d}/{m}" for d, m in examples)
            if count > 5:
                logger.warning(f"[DimensionResolver] {count} territorios no encontrados. Ejemplos: {examples_str}...")
            else:
                logger.warning(f"[DimensionResolver] Territorios no encontrados: {examples_str}")
    
    def log_campos_created_summary(self) -> None:
        """Loguea resumen de campos creados (llamar al final del proceso). DEPRECATED: usar log_summary()"""
        if self._campos_created_ids:
            summary = self._get_campos_created_summary()
            logger.info(f"[DimensionResolver] Campos creados: {summary}")
    
    def clear_caches(self) -> None:
        """Limpia todos los caches."""
        self._tiempo_cache.clear()
        self._territorio_cache.clear()
        self._campo_cache.clear()
        self._resolucion_cache.clear()
        self._campos_created_ids.clear()
        self._resoluciones_created_ids.clear()
        self._territorios_not_found.clear()
        logger.debug("[DimensionResolver] Caches limpiados")
