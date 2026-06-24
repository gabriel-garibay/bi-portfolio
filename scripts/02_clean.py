"""
Objetivo: limpieza y transformación de datos crudos
    data/raw -> data/clean (listos para carga a PostgreSQL)
"""

import pandas as pd
from pathlib import Path

# CONSTANTES

path_raw = Path("data/raw")
path_clean = Path("data/clean")

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


order_dates = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

# FUNCIONES DE LIMPIEZA


def limpiar_customers(df: pd.DataFrame) -> pd.DataFrame:
    # Estandarizar zip code en 5 dígitos
    df["customer_zip_code_prefix"] = (
        df["customer_zip_code_prefix"].astype(str).str.zfill(5)
    )
    # Normalizar ciudad y estado (city en minusculas, state en mayusc)
    df["customer_city"] = df["customer_city"].str.strip().str.lower()
    df["customer_state"] = df["customer_state"].str.strip().str.upper()
    return df


def limpiar_geolocation(df: pd.DataFrame) -> pd.DataFrame:
    # Eliminar duplicados exactos
    df = df.drop_duplicates()
    df["geolocation_zip_code_prefix"] = (
        df["geolocation_zip_code_prefix"].astype(str).str.zfill(5)
    )
    df["geolocation_city"] = df["geolocation_city"].str.strip().str.lower()
    df["geolocation_state"] = df["geolocation_state"].str.strip().str.upper()
    return df


def limpiar_order_items(df: pd.DataFrame) -> pd.DataFrame:
    df["shipping_limit_date"] = pd.to_datetime(
        df["shipping_limit_date"], errors="coerce"
    )
    return df


def limpiar_payments(df: pd.DataFrame) -> pd.DataFrame:
    df["payment_type"] = df["payment_type"].astype("category").str.strip().str.lower()
    return df


def limpiar_reviews(df: pd.DataFrame) -> pd.DataFrame:
    # Rating 1-5
    # df["review_score"] = df["review_score"].astype("int8") Se definirá en el DDL SQL
    df["review_creation_date"] = pd.to_datetime(
        df["review_creation_date"], errors="coerce"
    )
    df["review_answer_timestamp"] = pd.to_datetime(
        df["review_answer_timestamp"], errors="coerce"
    )
    return df


def limpiar_orders(df: pd.DataFrame) -> pd.DataFrame:
    df["order_status"] = df["order_status"].astype("category").str.strip().str.lower()
    # Convertir todas las columnas de fecha a datetime
    for col in order_dates:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def limpiar_products(df: pd.DataFrame) -> pd.DataFrame:
    # Rellenar NaN con "sin_categoria"
    df["product_category_name"] = (
        df["product_category_name"].fillna("sin_categoria").str.strip().str.lower()
    )
    # Cantidades enteras pequeñas
    df["product_name_lenght"] = df["product_name_lenght"].fillna(0)
    df["product_description_lenght"] = df["product_description_lenght"].fillna(0)
    df["product_photos_qty"] = df["product_photos_qty"].fillna(0)
    # Rellenar dimensiones físicas según mediana
    physical_cols = [
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]
    for col in physical_cols:
        cat_median = df.groupby("product_category_name")[col].transform("median")
        global_median = df[col].median()
        # ("sin_Categoria" -> mediana global)
        df.loc[df["product_category_name"] == "sin_categoria", col] = df.loc[
            df["product_category_name"] == "sin_categoria", col
        ].fillna(global_median)
        df[col] = df[col].fillna(cat_median)
    return df


def limpiar_sellers(df: pd.DataFrame) -> pd.DataFrame:
    df["seller_zip_code_prefix"] = df["seller_zip_code_prefix"].astype(str).str.zfill(5)
    df["seller_city"] = df["seller_city"].str.strip().str.lower()
    df["seller_state"] = df["seller_state"].str.strip().str.upper()
    return df


def limpiar_translations(df: pd.DataFrame) -> pd.DataFrame:
    # Normalizar strings para garantizar consistencia en joins con PRODUCTS
    df["product_category_name"] = (
        df["product_category_name"].astype("category").str.strip().str.lower()
    )
    df["product_category_name_english"] = (
        df["product_category_name_english"].astype("category").str.strip().str.lower()
    )
    return df


# MAPA NOMBRE → FUNCIÓN
fx_clean = {
    "customers": limpiar_customers,
    "geolocation": limpiar_geolocation,
    "order_items": limpiar_order_items,
    "payments": limpiar_payments,
    "reviews": limpiar_reviews,
    "orders": limpiar_orders,
    "products": limpiar_products,
    "sellers": limpiar_sellers,
    "translations": limpiar_translations,
}


def ver_limpios(nombre: str, df: pd.DataFrame) -> None:
    print(f"{nombre.upper()}")
    print(f"Filas: {len(df):,}  |  Columnas: {len(df.columns)}")

    nulos = df.isnull().sum()
    nulos_pct = (nulos / len(df) * 100).round(2)
    long_max = df.apply(
        lambda col: (
            col.max()
            if pd.api.types.is_numeric_dtype(col)
            else col.astype(str).str.len().max()
        ).astype(int)
    )
    reporte = pd.DataFrame(
        {
            "nulos": nulos,
            "pct_nulos": nulos_pct,
            "unicos": df.nunique(),
            "dtype": df.dtypes,
            "long/max": long_max,
        }
    )
    if reporte["nulos"].sum() > 0:
        print(f"{reporte.to_string()}\n")
    else:
        print(reporte.drop(columns=["nulos", "pct_nulos"]).to_string())
        print("Sin nulos.\n")


def main() -> None:

    for nombre, archivo in archivos.items():
        filepath = path_raw / archivo

        if not filepath.exists():
            print(f"No se encontró {archivo}\n")
            continue

        df = pd.read_csv(filepath)
        filas_antes = len(df)

        df = fx_clean[nombre](df)

        filas_despues = len(df)

        # Reporte de verificación para csv generados
        ver_limpios(nombre, df)

        output_path = path_clean / archivo
        df.to_csv(output_path, index=False)

        if nombre.upper() == "GEOLOCATION":
            print(f"Filas: {filas_antes:,} → {filas_despues:,}")
        print(f"Guardado: {output_path}\n")


if __name__ == "__main__":
    main()
