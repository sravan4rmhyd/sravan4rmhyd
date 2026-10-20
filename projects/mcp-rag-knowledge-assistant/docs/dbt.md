# dbt
dbt transforms data inside the warehouse using SQL models, tests and documentation.
Incremental models process only new rows, which keeps large Snowflake builds cheap.
Generic tests such as unique and not_null catch data quality issues before dashboards break.
