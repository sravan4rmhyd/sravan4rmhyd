import pytest
from pyspark.sql import SparkSession

from lakehouse.quality import Rule, split_valid_invalid


@pytest.fixture(scope="module")
def spark():
    s = SparkSession.builder.master("local[1]").config("spark.ui.enabled", "false").getOrCreate()
    yield s
    s.stop()


def test_rows_split_and_failures_are_named(spark):
    df = spark.createDataFrame([(1, 10.0), (2, -1.0), (None, 5.0)], "id int, amount double")
    rules = [Rule("id_not_null", "id IS NOT NULL"), Rule("amount_positive", "amount > 0")]
    valid, invalid = split_valid_invalid(df, rules)
    assert valid.count() == 1
    reasons = {tuple(r._failed_rules) for r in invalid.collect()}
    assert reasons == {("amount_positive",), ("id_not_null",)}
