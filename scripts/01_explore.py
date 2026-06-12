"""
Objetivo: entender la estructura, tipos de datos y calidad de cada tabla del
    dataset Brazilian E-Commerce antes de limpiar
    + EDA (products) / eliminar duplicados (geolocation)
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


# Capturar largo estándar del código zip_code_prefix
def explore_len() -> None:
    geolocation = pd.read_csv(path_raw / "olist_geolocation_dataset.csv")
    products = pd.read_csv(path_raw / "olist_products_dataset.csv")
    order_items = pd.read_csv(path_raw / "olist_order_items_dataset.csv")
    payments = pd.read_csv(path_raw / "olist_order_payments_dataset.csv")
    reviews = pd.read_csv(path_raw / "olist_order_reviews_dataset.csv")
    orders = pd.read_csv(path_raw / "olist_orders_dataset.csv")
    sellers = pd.read_csv(path_raw / "olist_sellers_dataset.csv")
    translations = pd.read_csv(path_raw / "product_category_name_translation.csv")
    # customer = pd.read_csv(path_raw / "olist_customers_dataset.csv")
    # Verificar longitud máxima del zip_code
    max_len_zip = geolocation["geolocation_zip_code_prefix"].astype(str).str.len().max()
    print(f"El largo máximo de zip_code_prefix es: {max_len_zip}")
    # Verificar que los productos sin dimensiones físicas aparecen en Order Items
    sin_medidas = products[products["product_weight_g"].isnull()]
    print(sin_medidas["product_id"].isin(order_items["product_id"]))


# Diagnóstico acerca de las medidas físicas como discrimante para categoría de producto
# Método: Random Forest como clasificador diagnóstico + cross-validation estratificada
def ml_products() -> None:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import StratifiedKFold, cross_validate
    from sklearn.preprocessing import LabelEncoder

    product_metricas = [
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]

    products = pd.read_csv(path_raw / "olist_products_dataset.csv")

    # El modelo se entrena solo con los que tienen categoría Y métricas completas
    con_cat = products.dropna(
        subset=["product_category_name"] + product_metricas
    ).copy()

    # Excluir categorías con menos de 5 muestras: StratifiedKFold(k=5)
    freq = con_cat["product_category_name"].value_counts()
    cats_validas = freq[freq >= 5].index
    con_cat = con_cat[con_cat["product_category_name"].isin(cats_validas)].copy()

    print("\nSe excluyeron categorías por muestras insuficientes (<5)")
    print(f"Categorías incluidas en diagnóstico : {len(cats_validas)}")
    print(f"Productos en entrenamiento          : {len(con_cat):,}")
    # Referencias (Baselines)
    bl_accuracy = freq.iloc[0] / len(con_cat)  # siempre predice la más frecuente
    bl_f1macro = 1 / len(cats_validas)  # aleatoriamente igual para cada categoría

    X = con_cat[product_metricas].values  # matriz de métricas físicas
    le = LabelEncoder()
    y = le.fit_transform(
        con_cat["product_category_name"]
    )  # categorías codificadas como enteros (LabelEncoder)

    # Parámetros de modelo
    rf = RandomForestClassifier(
        n_estimators=100,  # número de árboles
        class_weight="balanced",  # compensa desbalance entre frecuencias de categoria
        random_state=42,
        n_jobs=-1,  # usa todos los núcleos disponibles
    )

    # StratifiedKFold: divide en 5 partes manteniendo proporción de clases en cada parte
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Ejecutar cross-validation
    resultados = cross_validate(
        rf,
        X,
        y,
        cv=cv,
        scoring=["accuracy", "f1_macro"],
        return_train_score=False,
    )

    acc_media = resultados["test_accuracy"].mean()
    acc_std = resultados["test_accuracy"].std()
    f1_media = resultados["test_f1_macro"].mean()
    f1_std = resultados["test_f1_macro"].std()

    print("\nRESULTADOS (promedio de 5 folds):")
    print(f"Accuracy: {acc_media:.1%} ± {acc_std:.1%} (baseline: {bl_accuracy:.1%})")
    print(f"F1-macro: {f1_media:.1%} ± {f1_std:.1%} (baseline: {bl_f1macro:.1%})")

    # Entrenar sobre el dataset completo para obtener importancias estables
    rf.fit(X, y)
    importancias = pd.Series(
        rf.feature_importances_, index=product_metricas
    ).sort_values(ascending=False)

    print("\nIMPORTANCIA DE CADA MÉTRICA:")
    for feature, valor in importancias.items():
        print(f"{feature:<28} {valor:.1%}")


# Ejecución directa: python scripts/01_explore.py
if __name__ == "__main__":
    # main()
    # ml_products()
    explore_len()
