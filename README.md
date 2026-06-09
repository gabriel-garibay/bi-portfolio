# exploration_01
    Se observan tablas con cantidades aceptables de nulos considerando el nombre de campo o columna; sin embargo, nulos significativos en una tabla de dimensión (PRODUCTS) requieren análisis extra.
        610 nulos en product_category_name
        2 nulos en campos de métricas (weight, length, height, width)
    También, 1 M de filas en GEOLOCATION se requieren revisar por potenciales duplicados
        Filas: 1,000,163
        geolocation_zip_code_prefix: 19015 únicos
        
# exploration_02
    Se evaluó la separabilidad de product_category_name mediante las métricas físicas (weight, length, height, width) usando Random Forest como diagnóstico de separabilidad (70 categorías, n=32334, StratifiedKFold k=5, class_weight=balanced).
        Accuracy=34.3%, F1-macro=22.9%.
    Aunque el modelo supera el baseline aleatorio (F1 1.4%), un 65% de error en la asignación hace la imputación no confiable para uso analítico.
        Los 610 productos sin categoría se etiquetan como "sin_categoria".

# clean_01
    Funciones para cambio de datos realizadas, previa exploración de longitudes de datos numéricos y categorización de cadenas de texto.
    