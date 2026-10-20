"""Declarative data-quality gates: failing rows are quarantined, not dropped silently."""
from dataclasses import dataclass

from pyspark.sql import DataFrame
import pyspark.sql.functions as F


@dataclass(frozen=True)
class Rule:
    name: str
    condition: str  # SQL expression that must be TRUE for a valid row


def split_valid_invalid(df: DataFrame, rules: list[Rule]) -> tuple[DataFrame, DataFrame]:
    """Return (valid, quarantined). Quarantined rows carry the list of failed rules."""
    checks = F.array(*[F.when(~F.coalesce(F.expr(r.condition), F.lit(False)), F.lit(r.name)) for r in rules])
    failed = F.filter(checks, lambda x: x.isNotNull())
    tagged = df.withColumn("_failed_rules", failed)
    valid = tagged.filter(F.size("_failed_rules") == 0).drop("_failed_rules")
    invalid = tagged.filter(F.size("_failed_rules") > 0)
    return valid, invalid
