import pandas as pd
from pg_load import get_connection


# Assessment of a physical measurements as a discriminant for product categories.
# Method: Random Forest as a diagnostic classifier + cross-validation stratified
def ml_products(conn) -> dict:

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import StratifiedKFold, cross_validate
    from sklearn.preprocessing import LabelEncoder

    product_metricas = [
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]

    columnas = ["product_category_name"] + product_metricas
    query = f"SELECT {', '.join(columnas)} FROM bronze.products"
    products = pd.read_sql(query, conn)

    products[product_metricas] = (
        products[product_metricas]
        .replace("", pd.NA)
        .apply(pd.to_numeric, errors="coerce")
    )

    # The model is trained only on items that have a category and complete metrics
    con_cat = products.dropna(
        subset=["product_category_name"] + product_metricas
    ).copy()

    # Exclude categories with fewer than 5 samples: StratifiedKFold(k=5)
    freq = con_cat["product_category_name"].value_counts()
    cats_validas = freq[freq >= 5].index
    con_cat = con_cat[con_cat["product_category_name"].isin(cats_validas)].copy()

    print("\nCategories with insufficient samples were excluded (<5)")
    print(f"Categories included in the diagnostic: {len(cats_validas)}")
    print(f"Products in training: {len(con_cat):,}")
    # Baselines
    freq_post_filtro = con_cat["product_category_name"].value_counts()
    bl_accuracy = freq_post_filtro.iloc[0] / len(
        con_cat
    )  # It always predicts the most frequent one
    bl_f1macro = 1 / len(cats_validas)  # randomly equal for each category

    X = con_cat[product_metricas].values  # physical metrics matrix
    le = LabelEncoder()
    y = le.fit_transform(
        con_cat["product_category_name"]
    )  # categories encoded as integers (LabelEncoder)

    # Model parameters
    rf = RandomForestClassifier(
        n_estimators=100,  # number of trees
        class_weight="balanced",  # compensates for category frequency imbalance
        random_state=42,
        n_jobs=-1,  # use all available cores
    )

    # StratifiedKFold: Split into 5 parts, maintaining the class proportion in each part
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Execute cross-validation
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

    print("\nRESULTS (average of 5 folds):")
    print(f"Accuracy: {acc_media:.1%} ± {acc_std:.1%} (baseline: {bl_accuracy:.1%})")
    print(f"F1-macro: {f1_media:.1%} ± {f1_std:.1%} (baseline: {bl_f1macro:.1%})")

    # Train on the full dataset to obtain stable importance values
    rf.fit(X, y)
    importancias = pd.Series(
        rf.feature_importances_, index=product_metricas
    ).sort_values(ascending=False)

    for feature, valor in importancias.items():
        print(f"{feature:<28} {valor:.1%}")
    return {
        "n_categorias": len(cats_validas),
        "n_productos": len(con_cat),
        "baseline_accuracy": bl_accuracy,
        "baseline_f1_macro": bl_f1macro,
        "accuracy_mean": acc_media,
        "accuracy_std": acc_std,
        "f1_macro_mean": f1_media,
        "f1_macro_std": f1_std,
        "feature_importances": importancias.to_dict(),
    }


if __name__ == "__main__":
    conn = get_connection()
    try:
        resultados = ml_products(conn)
        print(resultados)
    finally:
        conn.close()
