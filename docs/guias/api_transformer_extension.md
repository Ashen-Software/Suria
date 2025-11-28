# Extender ApiTransformer - Guía Rápida

ApiTransformer es **genérico y parametrizado**. Para soportar una nueva API Socrata, solo necesitas:

1. **Definir configuración en `config.py`**
2. **Registrar en `CONFIG_REGISTRY`**
3. **Usar sin cambios de código**

## Paso 1: Crear TransformationConfig

En `data/workflows/full_etl/transformers/config.py`:

```python
from datetime import date

# Ejemplo: Nueva API de Oferta de Gas

def _derive_fecha_oferta(row):
    """Derivar fecha primer día del mes para oferta."""
    return date(int(row["anio"]), int(row["mes"]), 1)

def _validate_oferta_coherencia(record: Dict[str, Any]) -> Optional[str]:
    """Validar lógica específica de oferta."""
    # Ejemplo: producción >= reservas
    if record.get("produccion", 0) < record.get("reservas", 0):
        return "Producción menor que reservas"
    return None

OFERTA_CONFIG = TransformationConfig(
    source_id="api_oferta",
    description="ANH - Oferta de Gas (Socrata)",
    data_path="data",
    
    column_validations=[
        ColumnValidation("mes", ValidationRule.RANGE, 
                        "Mes fuera de rango (1-12)",
                        params={"min": 1, "max": 12}),
        ColumnValidation("produccion", ValidationRule.NON_NEGATIVE, 
                        "Producción negativa"),
        ColumnValidation("tipo_recurso", ValidationRule.ENUM, 
                        "Tipo recurso inválido",
                        params={"values": ["GN", "GC", "CR"]}),
    ],
    
    column_derivations=[
        ColumnDerivation(
            target_column="fecha_derivada",
            source_columns=["anio", "mes"],
            function=_derive_fecha_oferta,
            description="Derivar fecha primer día del mes"
        ),
    ],
    
    fact_mapping=FactTableMapping(
        fact_table="fact_demanda_gas_natural",
        column_mapping={
            "fecha": "fecha_derivada",
            "categoria": "categoria",
            "region": "region",
            "nodo": "nodo",
            "escenario": "escenario",
            "valor": "valor",
            "revision": "revision",
        },
        dimension_mappings=[
            DimensionMapping(
                dimension_name="tiempo",
                column_mapping={
                    "fecha": "fecha_derivada",
                    "anio": "anio",
                    "mes": "mes",
                    "es_proyeccion": True,
                }
            ),
            # Agregar más dimensiones según necesidad
        ],
        description="Fact table de demanda gas natural"
    ),
    
    custom_validator=_validate_oferta_coherencia,
)
```

## Paso 2: Registrar la Configuración

```python
# Al final de config.py

CONFIG_REGISTRY["api_oferta"] = OFERTA_CONFIG

# O usar función helper
register_transformation_config(OFERTA_CONFIG)
```

## Paso 3: Usar sin cambios de código

```python
from workflows.full_etl.transformers import ApiTransformer

transformer = ApiTransformer()

# ApiTransformer automáticamente busca "api_oferta" en CONFIG_REGISTRY
result = transformer.transform(
    raw_data=json_data_string,
    source_config={"id": "api_oferta"}
)

# result = {
#     "valid_records": [...],
#     "errors": [...],
#     "stats": {...}
# }
```

## Tipos de Validación Disponibles

| Tipo | Parámetros | Ejemplo |
|------|-----------|---------|
| `RANGE` | `min`, `max` | Mes 1-12 |
| `ENUM` | `values` (list) | Tipo: ["G", "O"] |
| `NON_NEGATIVE` | - | Precio >= 0 |
| `BETWEEN_0_100` | - | Porcentaje 0-100 |
| `POSITIVE` | - | Cantidad > 0 |
| `NOT_NULL` | - | Campo obligatorio |
| `DATE_VALID` | - | Fecha válida |

## Derivaciones Parametrizadas

```python
ColumnDerivation(
    target_column="new_column",
    source_columns=["col1", "col2"],  # Pasadas a function
    function=lambda row: row["col1"] * row["col2"],  # O función custom
    description="Multiplicación de columnas"
)
```

## Custom Validator (Lógica compleja)

```python
def _my_custom_validator(record: Dict[str, Any]) -> Optional[str]:
    """
    Validación cross-columna después de mapeo.
    
    Args:
        record: Dict con datos mapeados
        
    Returns:
        None si válido, string con mensaje de error si inválido
    """
    # Ejemplo: validar relaciones entre campos
    if record["produccion"] > record["capacidad"]:
        return "Producción excede capacidad"
    
    # Validar rango de fechas
    if record["fecha"] < date(2020, 1, 1):
        return "Fecha anterior a 2020"
    
    return None  # ✅ Válido
```

Asignar en config:
```python
fact_mapping=FactTableMapping(...),
custom_validator=_my_custom_validator,
```

## Custom Transformer (Transformación especial)

```python
def _my_custom_transformer(row: Dict[str, Any], source_id: str) -> Dict[str, Any]:
    """
    Transformación custom si las reglas no son suficientes.
    
    Args:
        row: DataFrame row como dict
        source_id: ID de la fuente
        
    Returns:
        {"fact_table": "...", "data": {...}, "dimensions": {...}}
    """
    return {
        "fact_table": "fact_custom",
        "data": {
            "campo1": row["col1"],
            "campo2": row["col2"] * 2,  # Transformación custom
        },
        "dimensions": {
            "tiempo": {...}
        }
    }
```

Asignar en config:
```python
custom_transformer=_my_custom_transformer,
```

## Checklist para Nueva Fuente

- [ ] Definir `TransformationConfig` en `config.py`
- [ ] Listar todas las validaciones necesarias
- [ ] Derivar columnas si aplica
- [ ] Mapear fact table + dimensiones
- [ ] Agregar custom_validator si hay lógica cross-columna
- [ ] Registrar en `CONFIG_REGISTRY`
- [ ] Probar: `transformer.transform(data, {"id": "api_nuevo"})`
- [ ] Documentar en tabla de fuentes

## Troubleshooting

**Error: "No hay TransformationConfig para {source_id}"**
- Verificar que `source_id` esté registrado en `CONFIG_REGISTRY`
- Confirmar nombre exacto (sensible a mayúsculas)

**Errores en validación vectorizada**
- Verificar nombres de columnas en `column_validations`
- Confirmar que columnas existen en JSON original

**Derivaciones fallan**
- Validar que `source_columns` existen en DataFrame
- Probar función lambda en aislamiento primero

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                   ApiTransformer.transform()                    │
│                 (Genérico y dirigido por config)                │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
  ┌──────────────────┐               ┌──────────────────────┐
  │ source_config    │               │ get_transformation   │
  │ {"id": "api_X"}  │               │ _config(source_id)   │
  └────────┬─────────┘               └──────────┬───────────┘
           │                                    │
           │                                    ▼
           │                         ┌─────────────────────┐
           │                         │   CONFIG_REGISTRY   │
           │                         │  (Dict[str->config])│
           │                         └────────┬────────────┘
           │                                  │
           │                 ┌────────────────┼────────────────┐
           │                 │                │                │
           │                 ▼                ▼                ▼
           │          ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
           │          │ REGALIAS_   │ │ TEMPLATE_   │ │   CUSTOM     │
           │          │ CONFIG      │ │ SOCRATA_    │ │   CONFIGS    │
           │          │ (instancia) │ │ CONFIG      │ │              │
           │          └─────────────┘ └─────────────┘ └──────────────┘
           │
           └──────────────────────────────────────────┐
                                                      │
                ┌─────────────────────────────────────┘
                │
                ▼
    ┌──────────────────────────────────┐
    │ TRANSFORMATION PIPELINE          │
    │ (7 pasos coherentes)             │
    └──────────────┬───────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   ┌─────────────┐    ┌────────────────┐
   │ JSON Parsing│    │ Extract Records│
   │  (orjson)   │    │ from config    │
   └──────┬──────┘    └────────┬───────┘
          │                    │
          └──────────┬─────────┘
                     │
                     ▼
          ┌────────────────────────┐
          │ Load DataFrame         │
          │ (Vectorized ops ready) │
          └────────────┬───────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
   ┌─────────────────┐        ┌──────────────────┐
   │ Pre-Validations │        │ Column Derivations│
   │ (Vectorized)    │        │ (from config)    │
   │ Via ValidationRule│       └──────┬───────────┘
   └────────┬────────┘              │
            │                       │
            └───────────┬───────────┘
                        │
                        ▼
          ┌────────────────────────────┐
          │ Mapping & Final Assembly   │
          │ (Via FactTableMapping)     │
          └────────────┬───────────────┘
                       │
                       ▼
          ┌────────────────────────────┐
          │ Return Transform Result    │
          │ {valid, errors, stats}     │
          └────────────────────────────┘
```
