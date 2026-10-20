# Data Platform Accelerator

A small, reusable framework for **config-driven pipelines**: ingest sources, run dbt-style SQL models, enforce
data-quality checks with severities, and emit a machine-readable run report. Uses DuckDB so it runs anywhere with no infrastructure.

```yaml
# pipelines/demo.yml
sources: {raw_orders: data/orders.csv}
models:  [stg_orders, customer_revenue]
checks:
  stg_orders:
    - {type: relationships, column: customer_id, to: stg_customers.customer_id, severity: warn}
    - {type: accepted_range, column: amount, min: 0}
```

## Features
- **Declarative pipelines**: sources, model order and checks live in YAML; models are plain `.sql` files.
- **Quality checks**: `not_null`, `unique`, `accepted_range`, `relationships`, `row_count_min`, each with `error`/`warn` severity.
- **CI-friendly**: exit code 1 when an `error` check fails; `--report run.json` for monitoring.
- **Portable design**: the SQL is warehouse-agnostic and ports to Snowflake or Databricks SQL by swapping the connection.

## Run
```bash
pip install -e ".[dev]"
dpa pipelines/demo.yml --report run.json
pytest -q
```
