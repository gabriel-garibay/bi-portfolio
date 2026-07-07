import pandas as pd
from pathlib import Path
from itertools import combinations

# SOURCE
path_raw = Path("data/raw")
archivos = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "translations": "product_category_name_translation.csv",
}


def buscar_pk_compuesta(df: pd.DataFrame, max_columnas: int = 2) -> list[tuple]:
    for tam in range(2, max_columnas + 1):
        candidatas = []
        for combo in combinations(df.columns, tam):
            if df.duplicated(subset=list(combo)).sum() == 0:
                candidatas.append(combo)
        if candidatas:
            return candidatas  # it stops at the minimum size that works
    return []


# Data structure and quality
def explorar(nombre: str, filepath: Path) -> None:
    df = pd.read_csv(filepath)
    # Tabla: # filas y columnas
    print(f"{nombre.upper()}")
    print(f"Rows: {len(df):,}  |  Columns: {len(df.columns)}")

    # Nulls quantity [int]
    nulos = df.isnull().sum()
    # Percentage of nulls per column [float]
    nulos_pct = (nulos / len(df) * 100).round(2)
    # Show data types, nulls and unique values per table (index = column name)
    reporte = pd.DataFrame(
        {
            "dtype": df.dtypes,
            "nulls": nulos,
            "pct_nulls": nulos_pct,
            "unique": df.nunique(),
        }
    )

    # Print table summary (details of nulls only for those containing them)
    if reporte["nulls"].sum() > 0:
        print(f"{reporte.to_string()}\n")

    else:
        print(reporte.drop(columns=["nulls", "pct_nulls"]).to_string())
        print("No nulls.\n")

    # Potential PK (100% cardinality)
    pk_candidatas = [col for col in df.columns if df[col].nunique() == len(df)]
    if pk_candidatas:
        print(f"Possible PK (Uniquiness): {pk_candidatas}")
    else:
        compuestas = buscar_pk_compuesta(df)
        if compuestas:
            print(f"Without simple PK. Potential composite PK: {compuestas}")
        else:
            print("Without simple or composite PK — evaluate hash.")
    # Duplicados exactos (fila completa)
    dup_count = df.duplicated().sum()
    print(f"Duplicate rows: {dup_count:,} ({dup_count / len(df) * 100:.2f}%)\n")


def main() -> None:
    for nombre, archivo in archivos.items():
        filepath = path_raw / archivo
        # Avoid error if a CSV is missing
        if filepath.exists():
            explorar(nombre, filepath)
        else:
            print(f"\nWARNING: not found {archivo}")


if __name__ == "__main__":
    main()
