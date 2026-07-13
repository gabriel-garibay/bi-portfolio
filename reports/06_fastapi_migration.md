# FastAPI Migration Report: Bronze Extraction Layer
**Execution Date:** 2026-07-13
**Pipeline Status:** OK
**Scope:** Replace CSV file extraction with HTTP-based extraction, same output contract

---

## Objective

Migrate the bronze ingestion source from local CSV files to a FastAPI service, without altering any downstream logic (DDL, loading, bronze schema, silver/gold layers). This validates the interface-contract design principle established during bronze development: extractors are interchangeable as long as they yield the same dict shape.

---

## Architecture

- api/main.py (FastAPI service)
    - loads all 9 CSVs into memory at startup (lifespan context manager)
    - exposes 1 paginated endpoint per table (?page=&size=)
    - localhost only, not yet dockerized
- scripts/03_bronze_load_olist.py
    - extract_from_api(): paginated HTTP client, same Iterator[dict] contract
    - extract_from_csv(): retained as fallback/local-testing path
    - main() now calls extract_from_api() in production flow

## New / Modified Files

| File | Change |
|---|---|
| `shared/__init__.py` | New — enables `shared` as an importable package |
| `shared/table_map.py` | New — `TABLE_MAP` extracted here, single source of truth |
| `scripts/03_bronze_load_olist.py` | `TABLE_MAP` removed (now imported), `extract_from_api()` added, `main()` updated |
| `api/main.py` | New — FastAPI service, 8 paginated endpoints, lifespan-based startup |

---

## Key Design Decisions

### Shared `TABLE_MAP`
Originally defined inline in `03_bronze_load_olist.py`. Extracted to `shared/table_map.py` because both the ingestion script and the new FastAPI service need the same file→column→conflict_key mapping. Duplicating it would risk silent desync between the pipeline and the API if a column changes in only one place.

### Interface-contract extraction: `extract_from_csv()` vs `extract_from_api()`
Both share the exact same signature output — `Iterator[dict]`, same keys per row, same `_row_hash` handling for geolocation. `main()` required a single-line change to switch sources. `extract_from_csv()` is intentionally retained (not deleted) as a fallback path for local testing without the FastAPI service running.

### API: in-memory load at startup, not per-request file reads
Given the dataset's static nature and modest size (largest file: ~738K geolocation rows), all 9 CSVs are loaded into memory once via a `lifespan` context manager (the modern replacement for the deprecated `@app.on_event("startup")`). Trade-off: requires a server restart if source CSVs change on disk — acceptable for this static portfolio dataset.

### Pagination
All 8 endpoints (`exchange_rates` excluded — sourced from Frankfurter API, not CSV) support `?page=&size=` query params, capped at `size<=10000`. Required specifically for `geolocation` (738,332 rows) to avoid single-response payloads that would be impractical over HTTP.

### `--reload-dir api` flag
Running `uvicorn api.main:app --reload` without scoping watches the entire project tree by default, causing unwanted server reloads when editing unrelated files like `scripts/03_bronze_load_olist.py`. Fixed via `--reload --reload-dir api`, restricting file-watching to the API's own directory.

---

## Validation

Ran `scripts/03_bronze_load_olist.py` against the live FastAPI service (localhost).
Result: exact row-count parity with the original CSV-based load — confirms zero data drift from the source-swap.

| Table | Rows (CSV baseline) | Rows (via API) | Match |
|---|---:|---:|:---:|
| customers | 99,441 | 99,441 | OK |
| orders | 99,441 | 99,441 | OK |
| order_items | 112,650 | 112,650 | OK |
| order_payments | 103,886 | 103,886 | OK |
| order_reviews | 99,224 | 99,224 | OK |
| products | 32,951 | 32,951 | OK |
| sellers | 3,095 | 3,095 | OK |
| geolocation | 738,332 | 738,332 | OK |
| product_category_name_translation | 71 | 71 | OK |

`geolocation` alone required ~739 paginated requests (738,332 rows / 1,000 per page), confirmed via request logs on the FastAPI server terminal during the run.

---

## Known Limitations (current state)

- Server runs on localhost only; not yet containerized (planned: Docker).
- No authentication/rate limiting — acceptable for a local portfolio demo, not production-appropriate as-is.
- In-memory load means data staleness risk if CSVs change without a server restart.

---

## Next Steps (Backlog)

1. Dockerize the FastAPI service + pipeline.
2. Re-validate `extract_from_api()` against the containerized service.