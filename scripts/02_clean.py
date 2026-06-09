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
    "reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "translations": "product_category_name_translation.csv",
}


# FUNCIONES DE LIMPIEZA


def limpiar_customers(df: pd.DataFrame) -> pd.DataFrame:
    # Normalizar ciudad y estado (city en minusculas, state en mayusc)
    df["customer_zip_code_prefix"] = (
        df["customer_zip_code_prefix"].astype(str).str.zfill(5)
    )
    df["customer_city"] = df["customer_city"].str.strip().str.lower()
    df["customer_state"] = df["customer_state"].str.strip().str.upper()
    return df


def limpiar_geolocation(df: pd.DataFrame) -> pd.DataFrame:
    # Eliminar duplicados exactos (mismo zip, lat, lng, ciudad y estado)
    df = df.drop_duplicates()
    df["geolocation_zip_code_prefix"] = (
        df["geolocation_zip_code_prefix"].astype(str).str.zfill(5)
    )
    df["geolocation_lat"] = df["geolocation_lat"].astype("float32")
    df["geolocation_city"] = df["geolocation_city"].str.strip().str.lower()
    df["geolocation_state"] = df["geolocation_state"].str.strip().str.upper()
    return df


def limpiar_order_items(df: pd.DataFrame) -> pd.DataFrame:
    df["shipping_limit_date"] = pd.to_datetime(
        df["shipping_limit_date"], errors="coerce"
    )
    # Por seguridad, se dejan en float64
    df["price"] = df["price"].astype(float)
    df["freight_value"] = df["freight_value"].astype(float)
    return df
