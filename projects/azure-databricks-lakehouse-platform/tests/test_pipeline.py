import pytest

from lakehouse import pipeline
from lakehouse.spark import get_spark


@pytest.fixture(scope="module")
def spark():
    s = get_spark("tests")
    yield s
    s.stop()


def test_medallion_end_to_end(spark, tmp_path):
    base = str(tmp_path)
    pipeline.run(base, "data/raw")

    silver = {r.order_id: r for r in spark.read.format("delta").load(f"{base}/silver/orders").collect()}
    assert set(silver) == {"1001", "1002", "1003", "1006"}      # bad rows removed, dupes collapsed
    assert silver["1001"].status == "SHIPPED"                     # latest version wins

    quarantine = spark.read.format("delta").load(f"{base}/quarantine/orders")
    assert quarantine.count() == 3                                # negative amount, null id, bad status

    gold = {r.customer_id: r for r in spark.read.format("delta").load(f"{base}/gold/customer_value").collect()}
    assert gold["C1"].orders == 2 and gold["C1"].lifetime_value == 200.5
    assert "C3" not in gold and gold["C2"].orders == 1            # cancelled excluded
