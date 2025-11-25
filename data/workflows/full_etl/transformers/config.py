"""
Configuración parametrizada para transformadores de APIs.

Define mapeos de columnas, validaciones pre-Pydantic, derivaciones de campos,
y lógica de transformación para cada fuente de datos.

Esto permite reutilizar ApiTransformer genéricamente sin hardcodear detalles
de columnas o validaciones específicas de cada API.
"""
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class ValidationRule(str, Enum):
    """Tipos de validación pre-Pydantic (vectorizadas en pandas)."""
    NOT_NULL = "not_null"
    RANGE = "range"  # params: min, max
    ENUM = "enum"  # params: values
    POSITIVE = "positive"
    NON_NEGATIVE = "non_negative"
    BETWEEN_0_100 = "between_0_100"
    DATE_VALID = "date_valid"


@dataclass
class ColumnValidation:
    """Define validación para una columna en el DataFrame."""
    column: str
    rule: ValidationRule
    error_message: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ColumnDerivation:
    """Define derivación de nueva columna a partir de existentes."""
    target_column: str
    source_columns: List[str]
    function: Callable  # recibe fila, retorna valor derivado
    description: str


@dataclass
class DimensionMapping:
    """Mapeo de columnas a una dimensión (tiempo, territorio, campo)."""
    dimension_name: str  # "tiempo", "territorio", "campo"
    column_mapping: Dict[str, str]  # {"dimension_field": "df_column"}
    deduplication_key: Optional[List[str]] = None  # campos para hacer DISTINCT
    description: str = ""


@dataclass
class FactTableMapping:
    """Mapeo de DataFrame a tabla de hechos."""
    fact_table: str  # "fact_regalias", "fact_demanda_gas", etc.
    column_mapping: Dict[str, str]  # {"fact_column": "df_column"}
    dimension_mappings: List[DimensionMapping] = field(default_factory=list)
    description: str = ""


@dataclass
class TransformationConfig:
    """
    Configuración completa para transformar datos de una fuente API.
    
    Parametriza la lógica de validación, derivación y mapeo sin código custom.
    """
    source_id: str
    description: str
    
    # Estructura del JSON esperado
    data_path: str = "data"  # "data" para Socrata {"data": [...]}, None para lista directa
    
    # Pre-validaciones vectorizadas (antes de Pydantic)
    column_validations: List[ColumnValidation] = field(default_factory=list)
    
    # Derivaciones de columnas
    column_derivations: List[ColumnDerivation] = field(default_factory=list)
    
    # Mapeo a tabla de hechos y dimensiones
    fact_mapping: Optional[FactTableMapping] = None
    
    # Validador custom opcional (si la lógica es muy compleja para reglas)
    custom_validator: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None
    # Retorna None si válido, o string con error si inválido
    
    # Transformer custom opcional (si necesita lógica especial post-validación)
    custom_transformer: Optional[Callable[[Dict[str, Any], str], Dict[str, Any]]] = None
    # Retorna dict con {"fact_table": ..., "data": ..., "dimensions": ...}


# Configuraciones especificas

def _derive_fecha_regalias(row):
    """Derivar fecha primer día del mes para regalías."""
    from datetime import date
    return date(int(row["a_o"]), int(row["mes"]), 1)


def _validate_regalias_coherencia(record: Dict[str, Any]) -> Optional[str]:
    """Validar coherencia especial de volumen_regalia vs producción."""
    # Opcional: validar que volumen_regalia sea aprox. producción * porcentaje / 100
    # Para esta demo solo retornamos None (válido)
    return None


# Configuracion para ANH Regalias (Socrata)
REGALIAS_CONFIG = TransformationConfig(
    source_id="api_regalias",
    description="ANH - Consolidación de regalías por campo (Socrata)",
    data_path="data",
    
    column_validations=[
        ColumnValidation("mes", ValidationRule.RANGE, "Mes fuera de rango (1-12)",
                        params={"min": 1, "max": 12}),
        ColumnValidation("tipohidrocarburo", ValidationRule.ENUM, "Tipo hidrocarburo inválido",
                        params={"values": ["G", "O"]}),
        ColumnValidation("preciohidrocarburousd", ValidationRule.NON_NEGATIVE, "Precio negativo"),
        ColumnValidation("porcregalia", ValidationRule.BETWEEN_0_100, "Porcentaje regalía fuera de rango"),
    ],
    
    column_derivations=[
        ColumnDerivation(
            target_column="tiempo_fecha",
            source_columns=["a_o", "mes"],
            function=_derive_fecha_regalias,
            description="Derivar fecha primer día del mes"
        ),
    ],
    
    fact_mapping=FactTableMapping(
        fact_table="fact_regalias",
        column_mapping={
            "tiempo_fecha": "tiempo_fecha",
            "campo_nombre": "campo",
            "departamento": "departamento",
            "municipio": "municipio",
            "latitud": "latitud",
            "longitud": "longitud",
            "contrato": "contrato",
            "tipo_produccion": "tipoprod",
            "tipo_hidrocarburo": "tipohidrocarburo",
            "precio_usd": "preciohidrocarburousd",
            "porcentaje_regalia": "porcregalia",
            "produccion_gravable": "prodgravableblskpc",
            "volumen_regalia": "volumenregaliablskpc",
            "valor_regalias_cop": "regaliascop",
            "unidad": "Bls/Kpc",  # Valor por defecto
        },
        dimension_mappings=[
            DimensionMapping(
                dimension_name="tiempo",
                column_mapping={
                    "fecha": "tiempo_fecha",
                    "anio": "a_o",
                    "mes": "mes",
                    "es_proyeccion": False,
                },
                description="Dimensión temporal mensual"
            ),
            DimensionMapping(
                dimension_name="territorio",
                column_mapping={
                    "departamento": "departamento",
                    "municipio": "municipio",
                    "latitud": "latitud",
                    "longitud": "longitud",
                },
                deduplication_key=["departamento", "municipio"],
                description="Dimensión geográfica"
            ),
            DimensionMapping(
                dimension_name="campo",
                column_mapping={
                    "nombre_campo": "campo",
                    "contrato": "contrato",
                    "activo": True,
                },
                deduplication_key=["nombre_campo"],
                description="Dimensión de campos"
            ),
        ],
        description="Fact table de liquidación de regalías"
    ),
    
    custom_validator=_validate_regalias_coherencia,
)


# Plantilla para agregar nuevas APIs Socrata
TEMPLATE_SOCRATA_CONFIG = TransformationConfig(
    source_id="api_nueva",
    description="Nueva fuente API (plantilla)",
    data_path="data",
    
    column_validations=[
        # TODO: Definir validaciones específicas
    ],
    
    column_derivations=[
        # TODO: Definir derivaciones si aplica
    ],
    
    fact_mapping=FactTableMapping(
        fact_table="fact_nueva",
        column_mapping={
            # TODO: Mapear columnas RAW a destino
        },
        dimension_mappings=[
            # TODO: Definir dimensiones
        ],
        description="Descripción de la fact table"
    ),
)


# Registro de configuraciones

CONFIG_REGISTRY: Dict[str, TransformationConfig] = {
    "api_regalias": REGALIAS_CONFIG,
    # Agregar nuevas fuentes aquí
}


def get_transformation_config(source_id: str) -> Optional[TransformationConfig]:
    """Obtiene configuración de transformación para una fuente."""
    return CONFIG_REGISTRY.get(source_id)


def register_transformation_config(config: TransformationConfig) -> None:
    """Registra una nueva configuración de transformación."""
    CONFIG_REGISTRY[config.source_id] = config
