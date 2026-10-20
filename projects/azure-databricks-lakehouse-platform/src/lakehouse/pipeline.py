"""Medallion pipeline: raw CSV -> Bronze (as-is) -> Silver (clean, deduped) -> Gold (aggregates)."""
import argparse

from delta.tables import DeltaTable
from pyspark.sql import DataFrame, SparkSession
import pyspark.sql.functions as F
from pyspark.sql.window import Window

from lakehouse.quality import Rule, split_valid_invalid
from lakehouse.spark import get_spark

ORDER_RULES = [
    Rule("order_id_not_null", "order_id IS NOT NULL"),
    Rule("amount_positive", "amount > 0"),
    Rule("valid_status", "status IN ('NEW','SHIPPED','DELIVERED','CANCELLED')"),
]


def to_bronze(spark: SparkSession, raw_path: str, bronze_path: str) -> DataFrame:
    df = (
        spark.read.option("header", True).csv(raw_path)
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )
    df.write.format("delta").mode("append").save(bronze_path)
    return df


def to_silver(spark: SparkSession, bronze_path: str, silver_path: str, quarantine_path: str) -> None:
    bronze = spark.read.format("delta").load(bronze_path)
    typed = (
        bronze.select(
            F.col("order_id"),
            F.col("customer_id"),
            F.col("amount").cast("double").alias("amount"),
            F.upper(F.trim("status")).alias("status"),
            F.to_timestamp("updated_at").alias("updated_at"),
        )
    )
    valid, invalid = split_valid_invalid(typed, ORDER_RULES)
    invalid.write.format("delta").mode("overwrite").save(quarantine_path)

    # keep only the latest version of each order
    latest = valid.withColumn(
        "_rn", F.row_number().over(
            Window.partitionBy("order_id").orderBy(F.col("updated_at").desc())
        )
    ).filter("_rn = 1").drop("_rn")

    if DeltaTable.isDeltaTable(spark, silver_path):
        (DeltaTable.forPath(spark, silver_path).alias("t")
         .merge(latest.alias("s"), "t.order_id = s.order_id")
         .whenMatchedUpdateAll(condition="s.updated_at > t.updated_at")
         .whenNotMatchedInsertAll().execute())
    else:
        latest.write.format("delta").save(silver_path)


def to_gold(spark: SparkSession, silver_path: str, gold_path: str) -> None:
    silver = spark.read.format("delta").load(silver_path)
    (silver.filter("status != 'CANCELLED'")
     .groupBy("customer_id")
     .agg(F.count("*").alias("orders"), F.round(F.sum("amount"), 2).alias("lifetime_value"))
     .write.format("delta").mode("overwrite").save(gold_path))


def run(base: str, raw: str) -> None:
    spark = get_spark("medallion")
    to_bronze(spark, raw, f"{base}/bronze/orders")
    to_silver(spark, f"{base}/bronze/orders", f"{base}/silver/orders", f"{base}/quarantine/orders")
    to_gold(spark, f"{base}/silver/orders", f"{base}/gold/customer_value")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="/tmp/lakehouse")
    p.add_argument("--raw", default="data/raw")
    a = p.parse_args()
    run(a.base, a.raw)
