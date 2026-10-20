"""Config-driven pipeline runner: ingest -> transform (SQL models) -> data-quality checks -> run report."""
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import duckdb
import yaml


@dataclass
class CheckResult:
    model: str
    check: str
    column: str | None
    failed_rows: int
    severity: str

    @property
    def passed(self) -> bool:
        return self.failed_rows == 0


def _check_sql(model: str, c: dict) -> str:
    col, t = c.get("column"), c["type"]
    if t == "not_null":
        return f"SELECT COUNT(*) FROM {model} WHERE {col} IS NULL"
    if t == "unique":
        return f"SELECT COUNT(*) FROM (SELECT {col} FROM {model} GROUP BY {col} HAVING COUNT(*) > 1)"
    if t == "accepted_range":
        lo, hi = c.get("min", "-1e308"), c.get("max", "1e308")
        return f"SELECT COUNT(*) FROM {model} WHERE {col} < {lo} OR {col} > {hi}"
    if t == "relationships":
        tbl, tcol = c["to"].split(".")
        return f"SELECT COUNT(*) FROM {model} WHERE {col} IS NOT NULL AND {col} NOT IN (SELECT {tcol} FROM {tbl})"
    if t == "row_count_min":
        return f"SELECT CASE WHEN COUNT(*) >= {c['min']} THEN 0 ELSE 1 END FROM {model}"
    raise ValueError(f"unknown check type: {t}")


def run_pipeline(config_path: str, root: str = ".", db: str = ":memory:") -> dict:
    cfg = yaml.safe_load(Path(config_path).read_text())
    root_p = Path(root)
    con = duckdb.connect(db)
    report: dict = {"models": [], "checks": [], "ok": True}

    for name, path in cfg["sources"].items():
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_csv_auto(?, header=true)", [str(root_p / path)])

    for model in cfg["models"]:
        sql = (root_p / "models" / f"{model}.sql").read_text()
        start = time.perf_counter()
        con.execute(f"CREATE OR REPLACE TABLE {model} AS {sql}")
        rows = con.execute(f"SELECT COUNT(*) FROM {model}").fetchone()[0]
        report["models"].append({"model": model, "rows": rows, "seconds": round(time.perf_counter() - start, 4)})

    for model, checks in cfg.get("checks", {}).items():
        for c in checks:
            failed = con.execute(_check_sql(model, c)).fetchone()[0]
            res = CheckResult(model, c["type"], c.get("column"), failed, c.get("severity", "error"))
            report["checks"].append(asdict(res) | {"passed": res.passed})
            if not res.passed and res.severity == "error":
                report["ok"] = False
    report["_con"] = con
    return report


def summarize(report: dict) -> str:
    lines = [f"{m['model']}: {m['rows']} rows in {m['seconds']}s" for m in report["models"]]
    for c in report["checks"]:
        flag = "PASS" if c["passed"] else ("FAIL" if c["severity"] == "error" else "WARN")
        lines.append(f"[{flag}] {c['model']}.{c['column'] or ''} {c['check']} ({c['failed_rows']} failing)")
    return "\n".join(lines)


def main() -> int:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("config")
    p.add_argument("--root", default=".")
    p.add_argument("--report", help="write JSON run report here")
    a = p.parse_args()
    r = run_pipeline(a.config, a.root)
    print(summarize(r))
    if a.report:
        Path(a.report).write_text(json.dumps({k: v for k, v in r.items() if k != "_con"}, indent=2))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
