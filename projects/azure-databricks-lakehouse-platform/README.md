# Azure Databricks Lakehouse Platform

A compact, tested **medallion architecture** (Bronze → Silver → Gold) on **PySpark + Delta Lake**, deployable to
**Azure Databricks** with a Databricks Asset Bundle.

```
raw CSV ──► Bronze (as-is + lineage cols) ──► Silver (typed, validated, deduped via MERGE) ──► Gold (customer lifetime value)
                                                  └──► Quarantine (rows that failed a rule, with the rule names)
```

## What it demonstrates
- **Declarative data-quality gates** (`quality.py`): bad rows are quarantined with the failing rule names rather than silently dropped.
- **Idempotent Silver upserts** with Delta `MERGE`, keeping only the latest version of each key.
- **Environment-aware Spark session**: Delta-enabled locally, native session on Databricks.
- **Deployment as code**: `databricks.yml` defines an hourly job on a job cluster.
- **CI**: GitHub Actions runs the test suite.

## Run locally
```bash
pip install -e ".[dev]"
python -m lakehouse.pipeline --base /tmp/lakehouse --raw data/raw
pytest -q
```
Sample data in `data/raw` deliberately includes a negative amount, a null key, an invalid status and a duplicate order.

## Deploy
Set the workspace host and storage account in `databricks.yml`, then `databricks bundle deploy -t dev`.
