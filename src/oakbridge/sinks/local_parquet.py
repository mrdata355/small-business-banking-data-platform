from __future__ import annotations

import shutil
from pathlib import Path

from pyspark.sql import DataFrame, Window, functions as F


def _replace_directory(tmp_path: Path, target_path: Path) -> None:
    if target_path.exists():
        shutil.rmtree(target_path)
    tmp_path.rename(target_path)


def append_parquet(df: DataFrame, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.write.mode("append").parquet(path)


def upsert_latest_parquet(
    batch_df: DataFrame,
    target_path: str,
    key_columns: list[str],
    order_columns: list[str],
) -> None:
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    spark = batch_df.sparkSession
    if target.exists():
        existing = spark.read.parquet(str(target))
        combined = existing.unionByName(batch_df, allowMissingColumns=True)
    else:
        combined = batch_df

    ordering = [F.col(c).desc_nulls_last() for c in order_columns]
    window = Window.partitionBy(*key_columns).orderBy(*ordering)

    latest = (
        combined
        .withColumn("_row_number", F.row_number().over(window))
        .filter(F.col("_row_number") == 1)
        .drop("_row_number")
        .cache()
    )
    latest.count()

    tmp = target.with_name(target.name + "__tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    latest.write.mode("overwrite").parquet(str(tmp))
    latest.unpersist()
    _replace_directory(tmp, target)
