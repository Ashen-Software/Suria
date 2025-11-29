"""
Modelos Pydantic para validación de datos del pipeline ETL.

Define schemas para:
- Tablas de hechos (fact_regalias, fact_demanda_gas, fact_oferta_gas)
- Dimensiones (dim_tiempo, dim_campos, dim_territorios)
- Validación de constraints (CHECK, tipos de datos, rangos)
"""
from typing import Optional, List
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class TipoHidrocarburo(str, Enum):
    GAS = "G"
    PETROLEO = "O"


class EscenarioProyeccion(str, Enum):
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    BAJO = "BAJO"
    IC_95 = "IC_95"
    IC_68 = "IC_68"


class SectorDemanda(str, Enum):
    RESIDENCIAL = "RESIDENCIAL"
    TERCIARIO = "TERCIARIO"
    INDUSTRIAL = "INDUSTRIAL"
    PETROQUIMICA = "PETROQUIMICA"
    PETROLERO = "PETROLERO"
    GNV = "GNV"
    TERMOELECTRICO = "TERMOELECTRICO"
    REFINERIA = "REFINERIA"


class RegionDemanda(str, Enum):
    CENTRO = "CENTRO"
    COSTA = "COSTA"
    CQR = "CQR"
    NOROESTE = "NOROESTE"
    OCCIDENTE = "OCCIDENTE"
    ORIENTE = "ORIENTE"
    SUR = "SUR"
    TOLIMA_GRANDE = "TOLIMA_GRANDE"


class SegmentoDemanda(str, Enum):
    TOTAL = "TOTAL"
    PETROLERO = "PETROLERO"
    TERMOELECTRICO = "TERMOELECTRICO"
    NO_TERMOELECTRICO = "NO_TERMOELECTRICO"


class NivelAgregacion(str, Enum):
    NACIONAL = "nacional"
    SECTORIAL = "sectorial"
    REGIONAL = "regional"

# Dimensiones

class DimTiempoSchema(BaseModel):
    """Schema para dim_tiempo - granularidad mensual."""
    fecha: date
    anio: int = Field(ge=1900, le=2100)
    mes: int = Field(ge=1, le=12)
    nombre_mes: str
    es_proyeccion: bool = False
    
    @field_validator('nombre_mes')
    @classmethod
    def validate_nombre_mes(cls, v: str) -> str:
        meses_validos = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        if v not in meses_validos:
            raise ValueError(f"Nombre de mes inválido. Debe ser uno de: {', '.join(meses_validos)}")
        return v


class DimTerritorioSchema(BaseModel):
    """Schema para dim_territorios - geografía de Colombia."""
    departamento: str
    municipio: str
    latitud: Optional[Decimal] = Field(None, ge=-90, le=90, decimal_places=7)
    longitud: Optional[Decimal] = Field(None, ge=-180, le=180, decimal_places=7)
    divipola: Optional[str] = Field(None, min_length=5, max_length=5)


class DimCampoSchema(BaseModel):
    """Schema para dim_campos - campos petroleros/gasíferos."""
    nombre_campo: str
    contrato: Optional[str] = None
    operador: Optional[str] = None
    asociados: Optional[List[str]] = Field(default_factory=list)
    participacion_estado: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    territorio_id: Optional[int] = None
    activo: bool = True


# Tablas de hechos

class FactRegaliasSchema(BaseModel):
    """
    Schema para fact_regalias - liquidación de regalías por campo.
    Fuente: API Socrata ANH (j7js-yk74)
    """
    tiempo_fecha: date
    campo_nombre: str

    departamento: str
    municipio: str
    latitud: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitud: Optional[Decimal] = Field(None, ge=-180, le=180)

    contrato: Optional[str] = None
    
    # Hechos
    tipo_produccion: str  # QB/P/B/I/QI
    tipo_hidrocarburo: TipoHidrocarburo
    precio_usd: Decimal = Field(ge=0, decimal_places=4)
    porcentaje_regalia: Decimal = Field(ge=0, le=100, decimal_places=2)
    produccion_gravable: Decimal = Field(ge=0, decimal_places=4)
    volumen_regalia: Decimal = Field(ge=0, decimal_places=4)
    unidad: str = "Bls/Kpc"
    valor_regalias_cop: Decimal = Field(ge=0, decimal_places=2)
    
    # Metadata
    source_id: str
    
    @model_validator(mode='after')
    def validate_volumen_regalia(self):
        """Valida que volumen_regalia sea coherente con producción y porcentaje."""
        expected_volumen = (self.produccion_gravable * self.porcentaje_regalia) / 100
        # Tolerancia del 1% por redondeos
        tolerance = expected_volumen * Decimal('0.01')
        if abs(self.volumen_regalia - expected_volumen) > tolerance:
            # Solo warning, no falla la validación
            pass
        return self


class FactDemandaGasSchema(BaseModel):
    """
    Schema para fact_demanda_gas - proyecciones de demanda.
    Fuente: UPME - Anexo Proyección Demanda
    """
    tiempo_fecha: date
    
    # Atributos categóricos con CHECK constraints
    escenario: EscenarioProyeccion
    sector: SectorDemanda
    region: RegionDemanda
    segmento: SegmentoDemanda
    nivel_agregacion: NivelAgregacion
    
    # Hecho
    valor_demanda_gbtud: Decimal = Field(ge=0, decimal_places=6)
    
    # Metadata
    source_id: str


class TipoProduccionOferta(str, Enum):
    """Tipos de producción válidos para fact_oferta_gas."""
    PTDV = "PTDV"  # Producción Total Disponible para Venta
    PC_CONTRATOS = "PC_CONTRATOS"  # Producción Comprometida - Contratos consumo interno
    PC_EXPORTACIONES = "PC_EXPORTACIONES"  # Producción Comprometida - Exportaciones
    PC_REF_BARRANCA = "PC_REF_BARRANCA"  # Producción Comprometida - Refinería Barrancabermeja
    PC_REF_CARTAGENA = "PC_REF_CARTAGENA"  # Producción Comprometida - Refinería Cartagena
    PP = "PP"  # Potencial Producción (declarado por operador)
    GAS_OPERACION = "GAS_OPERACION"  # Gas consumido en operaciones del campo
    CIDV = "CIDV"  # Capacidad Instalada Disponible para Venta


class DimResolucionSchema(BaseModel):
    """
    Schema para dim_resoluciones - metadatos de resoluciones MinMinas.
    Cada resolución define un período de declaración de producción.
    """
    numero_resolucion: str
    fecha_resolucion: Optional[date] = None
    periodo_desde: date
    periodo_hasta: date
    titulo: Optional[str] = None
    url_pdf: Optional[str] = None
    url_soporte_magnetico: Optional[str] = None
    source_id: str


class FactOfertaGasSchema(BaseModel):
    """
    Schema para fact_oferta_gas - declaración de producción.
    Fuente: MinMinas - Declaración de Producción
    
    Actualizado para soportar:
    - Tipo de producción con CHECK constraint
    - Operador (puede diferir del operador principal si hay asociados)
    - Participación del Estado
    - Poder calorífico del campo
    """
    tiempo_fecha: date
    campo_nombre: str
    
    # Tipo de producción/destino
    tipo_produccion: TipoProduccionOferta
    
    # Operador (puede ser distinto del operador del campo)
    operador: str
    es_operador_campo: bool = True
    es_participacion_estado: bool = False
    
    # Valor de producción (en GBTUD, unidad normalizada)
    valor_gbtud: Decimal = Field(ge=0, decimal_places=6)
    
    # Metadata del campo (snapshot del Excel)
    poder_calorifico_btu_pc: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    
    # Referencia a resolución (número, no FK - se resuelve en loader)
    resolucion_number: Optional[str] = None
    
    # Metadata ETL
    source_id: str


class FactParticipacionCampoSchema(BaseModel):
    """
    Schema para fact_participacion_campo - participación de asociados y estado.
    Registra la participación de cada asociado por campo y período.
    """
    campo_nombre: str
    resolucion_number: str
    periodo_desde: date
    periodo_hasta: date
    asociado: str
    participacion_pct: Decimal = Field(ge=0, le=100, decimal_places=2)
    estado_pct: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    source_id: str


# Referencias

class RefUnidadSchema(BaseModel):
    """Schema para ref_unidades - factores de conversión."""
    codigo: str
    nombre: str
    factor_a_gbtud: Optional[Decimal] = Field(None, decimal_places=10)
    descripcion: Optional[str] = None


# Parsing

class SocrataApiRegaliasRawSchema(BaseModel):
    """
    Schema para validar estructura RAW del JSON de Socrata ANH.
    Mapea nombres de columnas del API a nuestro modelo interno.
    """
    departamento: str
    municipio: str
    latitud: Decimal
    longitud: Decimal
    a_o: int  # año
    mes: int
    contrato: str
    campo: str
    tipoprod: str
    tipohidrocarburo: str
    preciohidrocarburousd: Decimal
    porcregalia: Decimal
    prodgravableblskpc: Decimal
    volumenregaliablskpc: Decimal
    regaliascop: Decimal
    
    def to_fact_regalias(self, source_id: str) -> FactRegaliasSchema:
        """Convierte registro RAW de Socrata a FactRegaliasSchema."""
        from datetime import date
        
        # Crear fecha del primer día del mes
        fecha = date(self.a_o, self.mes, 1)
        
        return FactRegaliasSchema(
            tiempo_fecha=fecha,
            campo_nombre=self.campo,
            departamento=self.departamento,
            municipio=self.municipio,
            latitud=self.latitud,
            longitud=self.longitud,
            contrato=self.contrato,
            tipo_produccion=self.tipoprod,
            tipo_hidrocarburo=TipoHidrocarburo(self.tipohidrocarburo),
            precio_usd=self.preciohidrocarburousd,
            porcentaje_regalia=self.porcregalia,
            produccion_gravable=self.prodgravableblskpc,
            volumen_regalia=self.volumenregaliablskpc,
            valor_regalias_cop=self.regaliascop,
            source_id=source_id
        )
