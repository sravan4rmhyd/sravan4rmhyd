from dpa.engine import run_pipeline


def test_demo_pipeline_models_and_checks():
    r = run_pipeline("pipelines/demo.yml")
    rows = {m["model"]: m["rows"] for m in r["models"]}
    assert rows["stg_customers"] == 4          # exact duplicate removed
    by_check = {(c["model"], c["check"], c["column"]): c for c in r["checks"]}
    assert by_check[("stg_customers", "not_null", "name")]["failed_rows"] == 1   # warn
    assert by_check[("stg_orders", "relationships", "customer_id")]["failed_rows"] == 1  # orphan C9
    assert r["ok"] is True                     # only warnings failed

    con = r["_con"]
    rev = dict(con.execute("SELECT customer_id, revenue FROM customer_revenue").fetchall())
    assert rev["C1"] == 200.5 and rev["C3"] == 200.0


def test_error_severity_fails_pipeline(tmp_path):
    cfg = tmp_path / "p.yml"
    cfg.write_text(
        "sources: {raw_orders: data/orders.csv}\nmodels: [stg_orders]\n"
        "checks: {stg_orders: [{type: accepted_range, column: amount, min: 100}]}\n"
    )
    assert run_pipeline(str(cfg))["ok"] is False
