"""
Test rápido: Verificar que DataValidator funciona correctamente

Uso:
  python -m workflows.full_etl.transformers.test_data_cleaner
"""
import pandas as pd
from workflows.full_etl.transformers.data_cleaner import DataValidator


def test_data_cleaner():
    """Test simple del DataValidator."""
    
    print("=" * 70)
    print("[TEST] DataValidator - Limpieza Común")
    print("=" * 70)
    
    # Crear DataFrame crudo (como vendría de JSON)
    records = [
        {"mes": "1", "a_o": "2024", "campo": "  CAMPO A  ", "precio": "100.5", "tipo": "G"},
        {"mes": "13", "a_o": "2024", "campo": "CAMPO B", "precio": "-50", "tipo": "X"},
        {"mes": "", "a_o": "2024", "campo": "CAMPO C", "precio": "75.0", "tipo": "G"},
    ]
    
    df = pd.DataFrame(records)
    
    print("\n[1] DataFrame CRUDO:")
    print(df)
    print(f"\nTipos:\n{df.dtypes}")
    
    # Aplicar limpieza común
    print("\n[2] Aplicando limpieza común...")
    df_clean, errors = DataValidator.validate_and_clean(
        df=df,
        records=records,
        not_null_columns=["mes", "campo"],
        type_mapping={
            "mes": "int",
            "a_o": "int",
            "precio": "float",
        },
        normalize_strings=True
    )
    
    print("\n[3] DataFrame LIMPIO:")
    print(df_clean)
    print(f"\nTipos:\n{df_clean.dtypes}")
    
    print(f"\n[4] ERRORES DETECTADOS ({len(errors)}):")
    for err in errors:
        print(f"  - Fila {err['record_index']}: {err['error']}")
    
    print("\n" + "=" * 70)
    print("[RESULTADO]")
    if len(errors) > 0:
        print(f"✓ EXITO: DataValidator detectó {len(errors)} errores como se esperaba")
    else:
        print("✗ FALLO: No se detectaron errores")
    print("=" * 70)


if __name__ == "__main__":
    test_data_cleaner()
