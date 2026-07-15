# ML Category Diagnostic — Physical Dimensions as Category Predictor

## Objective

Assess whether physical product dimensions (weight, length, height, width) carry sufficient signal to predict `product_category_name`, as a candidate strategy for imputing category values left NULL because the source product has no category recorded.

## Method

| Item | Value |
|---|---|
| Model | RandomForestClassifier (n_estimators=100, class_weight="balanced", random_state=42) |
| Validation | StratifiedKFold (k=5, shuffle=True, random_state=42) via cross_validate |
| Scoring | accuracy, f1_macro |
| Source | bronze.products (raw mirror) |
| Filter | Rows with non-null category and complete physical dimensions; categories with fewer than 5 samples excluded (required for StratifiedKFold with k=5) |

## Dataset

| Metric | Value |
|---|---|
| Categories included | 71 |
| Products in training set | 32,943 |

## Results

| Metric | Model (5-fold mean ± std) | Baseline | Baseline method |
|---|---|---|---|
| Accuracy | 33.7% ± 0.3% | 9.2% | Predict most frequent category |
| F1-macro | 22.9% ± 1.0% | 1.4% | Uniform random across categories |

## Feature Importances

| Feature | Importance | Status |
|---|---|---|
| product_weight_g | 31.8% | Contributing |
| product_length_cm | 23.3% | Contributing |
| product_height_cm | 22.9% | Contributing |
| product_width_cm | 22.0% | Contributing |

## Interpretation

Model performance is substantially above both baselines (3.7x accuracy baseline, 16x F1-macro baseline). Physical dimensions carry non-trivial signal — no single dimension dominates, all four contribute within a narrow 22–32% range, suggesting the signal is a joint function of overall product size rather than one specific measurement.

However, absolute performance remains far below a production-usable threshold: 33.7% accuracy across 71 categories means roughly two out of three imputed labels would be wrong. F1-macro of 22.9% confirms this error is distributed across classes, not concentrated in a few rare ones.

## Decision

**Not adopted in production.** `product_category_name` remains `NULL` in gold whenever the source product has no category recorded.

## Justification

Physical dimensions correlate with category better than chance, but not well enough to replace a missing value with a confident prediction. Imputing an incorrect category silently corrupts downstream category-level metrics (`dim_products`, category aggregations in `fct_order_items`), whereas an explicit `NULL` is visible, filterable, and does not misrepresent the data.

## Scope

Diagnostic only, run against `bronze.products`. Parallel to the bronze → silver → gold pipeline; no production model, table, or dbt model depends on this output.

**Script:** `scripts/ml_category_diagnostic.py`