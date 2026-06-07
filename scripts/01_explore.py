"""
Objetivo: entender la estructura, tipos de datos y calidad de cada tabla del
    dataset Brazilian E-Commerce antes de limpiar.
"""

import pandas as pd
from pathlib import Path

# CONSTANTES

path_raw = Path("data/raw")  # Objeto de ruta, multiplataforma
# Titulos y ubicaciones de archivos a explorar
archivos = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "translations": "product_category_name_translation.csv",
}


# FUNCIÓN PRINCIPAL DE EXPLORACIÓN (Estructura y calidad de datos)
def explorar(nombre: str, filepath: Path) -> None:
    df = pd.read_csv(filepath)
    # Imprime nombre de la tabla
    print(f"{nombre.upper()}")
    # Imprime número de filas y columnas
    print(f"Filas: {len(df):,}  |  Columnas: {len(df.columns)}")

    # CALIDAD

    # pd.Series donde índice = nombre columna, valor = cantidad de nulos [int]
    nulos = df.isnull().sum()

    # pd.Series donde índice = nombre columna, valor = porcentaje de nulos por columna [float]
    nulos_pct = (nulos / len(df) * 100).round(2)

    # Mostrar tipo de datos, nulos y valores únicos por tabla (index = nombre columna)
    reporte = pd.DataFrame(
        {
            "dtype": df.dtypes,
            "nulos": nulos,
            "pct_nulos": nulos_pct,
            "unicos": df.nunique(),
        }
    )

    # Imprimir resumen de tablas (detalle de nulos solo para las que los contengan)
    if reporte["nulos"].sum() > 0:
        print(f"{reporte.to_string()}\n")

    else:
        print(reporte.drop(columns=["nulos", "pct_nulos"]).to_string())
        print("Sin nulos.\n")


# FUNCIÓN MAIN
def main() -> None:
    for nombre, archivo in archivos.items():
        filepath = path_raw / archivo
        # Evitar un error crudo de pandas si falta algún CSV
        if filepath.exists():
            explorar(nombre, filepath)
        else:
            print(f"\nADVERTENCIA: no se encontró {archivo}")


# Ejecución directa: python scripts/01_explore.py
if __name__ == "__main__":
    main()
