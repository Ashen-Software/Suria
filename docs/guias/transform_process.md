# Transform

Módulo de transformación de datos RAW a estructura normalizada para carga en PostgreSQL.

## Arquitectura

El módulo `transformers/` sigue el patrón Strategy, permitiendo transformaciones específicas según el tipo de fuente de datos:

```
transformers/
├── __init__.py          # Registry de transformers
├── base.py              # Clase abstracta BaseTransformer
├── schemas.py           # Modelos Pydantic para validación
├── api.py               # Transforma JSON de APIs (Socrata)
├── excel.py             # Transforma archivos Excel (UPME, MinMinas)
├── custom.py            # Ejecuta scripts custom
└── custom_scripts/      # Scripts de transformación personalizados
    └── __example_transformer.py
```

## Flujo de Transformación

```
┌─────────────────────┐
│   Archivo RAW       │ (JSON/Excel/bytes desde Supabase Storage)
│   (Storage)         │
└──────────┬──────────┘
           │
           ├─ get_transformer(source_type)
           ▼
┌─────────────────────┐
│   Transformer       │ (api.py / excel.py / custom.py)
│   (parse + validate)│
└──────────┬──────────┘
           │
           ├─ Parsear contenido según formato
           ├─ Validar con Pydantic schemas
           ▼
┌─────────────────────┐
│  Estructura         │ {"valid_records": [...],
│  Normalizada        │  "errors": [...],
│                     │  "stats": {...}}
└──────────┬──────────┘
           │
           ├─ Listo para Loader
           ▼
┌─────────────────────┐
│   PostgreSQL        │ (fact_regalias, fact_demanda_gas, etc.)
└─────────────────────┘
```

## Uso

### 1. Obtener Transformer

```python
from workflows.full_etl.transformers import get_transformer

# Obtener transformer según tipo de fuente
transformer = get_transformer("api")  # ApiTransformer
transformer = get_transformer("complex_scraper")  # CustomTransformer
```

### 2. Transformar Datos

```python
# Cargar datos RAW desde Storage
raw_data = supabase.storage.from_("raw-data").download("api/api_regalias/2024-11-25_120000.json")

# Transformar
result = transformer.transform(raw_data, source_config)

# Resultado
print(f"Válidos: {len(result['valid_records'])}")
print(f"Errores: {len(result['errors'])}")
```

### 3. Estructura del Resultado

```python
{
    "valid_records": [
        {
            "fact_table": "fact_regalias",
            "data": {
                "tiempo_fecha": "2024-01-01",
                "campo_nombre": "RUBIALES",
                "tipo_hidrocarburo": "G",
                "precio_usd": 3.45,
                ...
            },
            "dimensions": {
                "tiempo": {
                    "fecha": "2024-01-01",
                    "anio": 2024,
                    "mes": 1,
                    "es_proyeccion": False
                },
                "territorio": {
                    "departamento": "META",
                    "municipio": "ACACIAS",
                    "latitud": 3.98,
                    "longitud": -73.76
                },
                "campo": {
                    "nombre_campo": "RUBIALES",
                    "contrato": "LLANOS 5",
                    "activo": True
                }
            }
        },
        ...
    ],
    "errors": [
        {
            "record_index": 123,
            "error": "ValidationError: campo 'precio_usd' debe ser >= 0",
            "raw_record": {...}
        },
        ...
    ],
    "stats": {
        "total_raw": 1000,
        "valid": 995,
        "errors": 5,
        "processing_time_seconds": 12.5,
        "error_categories": {
            "Porcentaje regalía fuera de rango": 3,
            "Tipo hidrocarburo inválido": 2
        }
    }
}
```

## Transformers Disponibles

### ApiTransformer (`api.py`)

Transforma JSON de APIs (principalmente Socrata). **Genérico y parametrizado** mediante `TransformationConfig`.

**Fuentes soportadas:**
- `api_regalias` → ANH Consolidación de Regalías → `fact_regalias`
- Extensible: cualquier API Socrata registrando config en `CONFIG_REGISTRY`

**Características:**
- Parseo rápido con orjson (fallback a json)
- Pre-validaciones vectorizadas en pandas (masivas, eficientes)
- Derivación de columnas parametrizada
- Mapeo genérico a fact tables + dimensiones
- **Dirigido por config**: sin código hardcodeado por fuente

**Ejemplo de uso:**
```python
from workflows.full_etl.transformers import ApiTransformer

transformer = ApiTransformer()
result = transformer.transform(json_data, {"id": "api_regalias"})
```

### ExcelTransformer (`excel.py`)

Transforma archivos Excel (UPME, MinMinas).

**Fuentes soportadas:**
- `upme_demanda` → Proyección de Demanda → `fact_demanda_gas`
- `minminas_oferta` → Declaración de Producción → `fact_oferta_gas`

**Características:**
- Parseo con Pandas + OpenPyXL
- Soporte para múltiples hojas
- Conversión automática de unidades (KPCD/MPCD → GBTUD)
- Validación de CHECK constraints

**Ejemplo de uso:**
```python
from workflows.full_etl.transformers import ExcelTransformer

transformer = ExcelTransformer()
result = transformer.transform(excel_bytes, source_config)
```

### CustomTransformer (`custom.py`)

Ejecuta scripts de transformación personalizados.

**Convención:**
- Scripts en: `transformers/custom_scripts/{source_id}_transformer.py`
- Debe exponer: `transform(raw_data, source_config) → dict`

**Ejemplo de script custom:**
```python
# custom_scripts/banco_central_transformer.py

def transform(raw_data, source_config):
    valid_records = []
    errors = []
    
    # Tu lógica de transformación aquí
    
    return {
        "valid_records": valid_records,
        "errors": errors,
        "stats": {
            "total_raw": len(valid_records) + len(errors),
            "valid": len(valid_records),
            "errors": len(errors)
        }
    }
```

## Schemas de Validación (`schemas.py`)

### Tablas de Hechos

#### FactRegaliasSchema
```python
tiempo_fecha: date
campo_nombre: str
tipo_hidrocarburo: TipoHidrocarburo  # "G" o "O"
precio_usd: Decimal (ge=0, decimal_places=4)
porcentaje_regalia: Decimal (ge=0, le=100, decimal_places=2)
produccion_gravable: Decimal (ge=0, decimal_places=4)
volumen_regalia: Decimal (ge=0, decimal_places=4)
valor_regalias_cop: Decimal (ge=0, decimal_places=2)
```

#### FactDemandaGasSchema
```python
tiempo_fecha: date
escenario: EscenarioProyeccion  # MEDIO, ALTO, BAJO, IC_95, IC_68
sector: SectorDemanda  # RESIDENCIAL, INDUSTRIAL, etc.
region: RegionDemanda  # CENTRO, COSTA, etc.
segmento: SegmentoDemanda  # TOTAL, PETROLERO, etc.
nivel_agregacion: NivelAgregacion  # nacional, sectorial, regional
valor_demanda_gbtud: Decimal (ge=0, decimal_places=6)
```

#### FactOfertaGasSchema
```python
tiempo_fecha: date
campo_nombre: str
potencial_produccion: Decimal (ge=0, decimal_places=4)
unidad: str  # KPCD, MPCD, GBTUD
potencial_gbtud: Decimal (ge=0, decimal_places=6)
```

### Dimensiones

#### DimTiempoSchema
```python
fecha: date
anio: int (ge=1900, le=2100)
mes: int (ge=1, le=12)
nombre_mes: str  # "Enero", "Febrero", etc.
es_proyeccion: bool
```

#### DimTerritorioSchema
```python
departamento: str
municipio: str
latitud: Decimal (ge=-90, le=90, decimal_places=7)
longitud: Decimal (ge=-180, le=180, decimal_places=7)
divipola: str (min_length=5, max_length=5)
```

#### DimCampoSchema
```python
nombre_campo: str
contrato: str
operador: str
asociados: List[str]
participacion_estado: Decimal (ge=0, le=100, decimal_places=2)
territorio_id: int
activo: bool
```

## Agregar Nuevo Transformer

### 1. Para API nueva:

Editar `api.py`:
```python
def _get_transformer_function(self, source_id: str):
    transformers = {
        "api_regalias": self._transform_socrata_regalias,
        "nueva_api": self._transform_nueva_api,  # ← Agregar
    }
    return transformers.get(source_id, self._transform_generic_json)

def _transform_nueva_api(self, raw_record, source_id):
    # Tu lógica aquí
    pass
```

### 2. Para Excel nuevo:

Editar `excel.py`:
```python
def _get_transformer_function(self, source_id: str):
    transformers = {
        "upme_demanda": self._transform_upme_demanda,
        "minminas_oferta": self._transform_minminas_oferta,
        "nuevo_excel": self._transform_nuevo_excel,  # ← Agregar
    }
    return transformers.get(source_id, self._transform_generic_excel)

def _transform_nuevo_excel(self, excel_file, source_id):
    # Tu lógica aquí
    return valid_records, errors
```

### 3. Para script totalmente custom:

Crear archivo `custom_scripts/{source_id}_transformer.py` con función `transform()`.

## Validación de Datos

**En ApiTransformer (parametrizado):**
- Pre-validaciones vectorizadas en pandas (antes de mapear)
- Reglas definidas en `TransformationConfig.column_validations`
- Tipos: RANGE, ENUM, NON_NEGATIVE, BETWEEN_0_100, DATE_VALID, etc.
- Cada violación genera error sin detener procesamiento

**Ejemplo de regla de validación:**
```python
# En config.py
ColumnValidation(
    column="porcregalia",
    rule=ValidationRule.BETWEEN_0_100,
    error_message="Porcentaje regalía fuera de rango"
)
```

**En ExcelTransformer & CustomTransformer:**
- Pueden usar schemas Pydantic (e.g., `FactRegaliasSchema`)
- Validación exhaustiva post-extracción
- Genera `ValidationError` capturado en estructura de errores

## Manejo de Errores

Los transformers **NO detienen el procesamiento** ante errores de validación individual. En su lugar:

1. **Registro inválido** → Se agrega a `errors[]`
2. **Continúa procesando** siguientes registros
3. **Al final retorna** todos los válidos + todos los errores

Esto permite:
- Cargar datos parciales (registros válidos)
- Auditar errores para corrección manual
- No perder todo el batch por un solo registro corrupto

**Ejemplo de error:**
```python
{
    "record_index": 123,
    "error": "1 validation error for FactRegaliasSchema\nprecio_usd\n  Input should be greater than or equal to 0",
    "raw_record": {
        "departamento": "META",
        "campo": "RUBIALES",
        "precio_usd": -5.0,
        ...
    }
}
```

## Testing

```python
# Test básico de transformer
from workflows.full_etl.transformers import get_transformer

source_config = {
    "id": "api_regalias",
    "type": "api",
    ...
}

raw_data = '{"data": [{"departamento": "META", ...}]}'

transformer = get_transformer("api")
result = transformer.transform(raw_data, source_config)

assert result["stats"]["valid"] > 0
assert len(result["valid_records"]) == result["stats"]["valid"]
```

## Documentación Complementaria

- **`api_transformer_extension.md`**: Guía paso-a-paso para extender ApiTransformer a nuevas fuentes
