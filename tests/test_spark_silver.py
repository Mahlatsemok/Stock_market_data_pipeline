from datetime import date, datetime, timedelta, timezone
import os
from pathlib import Path
import sys

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)

from stock_processing import (
    run_gold,
    transform_gold,
    transform_gold_summary,
    transform_silver,
)


@pytest.fixture(scope="module")
def spark():
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
    session = (
        SparkSession.builder
        .master("local[2]")
        .appName("stock-silver-tests")
        .config("spark.ui.enabled", "false")
        .config("spark.pyspark.python", sys.executable)
        .config("spark.pyspark.driver.python", sys.executable)
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


@pytest.fixture
def bronze_schema():
    return StructType(
        [
            StructField("Date", StringType(), True),
            StructField("Adj Close", DoubleType(), True),
            StructField("Close", DoubleType(), True),
            StructField("High", DoubleType(), True),
            StructField("Low", DoubleType(), True),
            StructField("Open", DoubleType(), True),
            StructField("Volume", LongType(), True),
            StructField("Ticker", StringType(), True),
            StructField("ingested_at_utc", StringType(), True),
            StructField("source_system", StringType(), True),
        ]
    )


@pytest.fixture
def sample_rows():
    return [
        (
            "2025-01-01", 99.0, 100.0, 102.0, 98.0, 99.0,
            1000, "aapl", "2025-01-02T10:00:00+00:00", "yahoo_finance",
        ),
        (
            "2025-01-01", 100.0, 101.0, 103.0, 99.0, 100.0,
            1100, "AAPL", "2025-01-03T10:00:00+00:00", "yahoo_finance",
        ),
        (
            "2025-01-02", 101.0, 102.0, 104.0, 100.0, 101.0,
            1200, "AAPL", "2025-01-03T10:00:00+00:00", "yahoo_finance",
        ),
        (
            "2025-01-03", 102.0, 103.0, 99.0, 98.0, 100.0,
            1300, "AAPL", "2025-01-04T10:00:00+00:00", "yahoo_finance",
        ),
    ]


def test_silver_standardizes_tickers_and_keeps_latest_duplicate(
    spark, bronze_schema, sample_rows
):
    df = spark.createDataFrame(sample_rows, schema=bronze_schema)

    result = transform_silver(df).orderBy("Date").collect()

    assert len(result) == 2
    assert result[0]["Ticker"] == "AAPL"
    assert result[0]["Close"] == 101.0
    assert result[0]["Volume"] == 1100
    assert result[0]["Date"] == date(2025, 1, 1)


def test_silver_rejects_invalid_price_relationships(
    spark, bronze_schema, sample_rows
):
    df = spark.createDataFrame(sample_rows, schema=bronze_schema)

    result = transform_silver(df).collect()

    assert all(row["High"] >= row["Low"] for row in result)
    assert all(row["High"] >= row["Open"] for row in result)
    assert all(row["High"] >= row["Close"] for row in result)
    assert all(row["Low"] <= row["Open"] for row in result)
    assert all(row["Low"] <= row["Close"] for row in result)


def test_silver_preserves_metadata_and_optional_adjusted_close(
    spark, bronze_schema, sample_rows
):
    df = spark.createDataFrame(sample_rows[:1], schema=bronze_schema)

    row = transform_silver(df).first()

    assert row is not None
    assert row["source_system"] == "yahoo_finance"
    assert row["ingested_at_utc"] is not None
    assert row["Adj Close"] == 99.0


def test_silver_returns_empty_dataframe_when_all_rows_are_invalid(
    spark, bronze_schema, sample_rows
):
    invalid = list(sample_rows[0])
    invalid[2] = -1.0
    df = spark.createDataFrame([tuple(invalid)], schema=bronze_schema)

    assert transform_silver(df).count() == 0


def test_gold_calculates_returns_rolling_averages_and_ticker_summary(
    spark, bronze_schema
):
    start_date = date(2025, 1, 1)
    rows = []
    for index in range(20):
        close = 100.0 + index
        rows.append(
            (
                (start_date + timedelta(days=index)).isoformat(),
                close,
                close,
                close + 2.0,
                close - 2.0,
                close,
                1000 + index,
                "AAPL",
                "2025-01-21T10:00:00+00:00",
                "yahoo_finance",
            )
        )

    bronze_df = spark.createDataFrame(rows, schema=bronze_schema)
    silver_df = transform_silver(bronze_df)
    daily_gold_df = transform_gold(silver_df).orderBy("Date")
    daily_rows = daily_gold_df.collect()

    assert len(daily_rows) == 20
    assert daily_rows[0]["Daily_Return"] is None
    assert daily_rows[1]["Daily_Return"] == pytest.approx(1.0)
    assert all(row["MA5"] is None for row in daily_rows[:4])
    assert daily_rows[4]["MA5"] == pytest.approx(102.0)
    assert all(row["MA20"] is None for row in daily_rows[:19])
    assert daily_rows[19]["MA20"] == pytest.approx(109.5)
    assert daily_rows[19]["Year"] == 2025
    assert daily_rows[19]["Month"] == 1

    summary_rows = transform_gold_summary(daily_gold_df).collect()
    assert len(summary_rows) == 1
    summary = summary_rows[0]
    assert summary["Ticker"] == "AAPL"
    assert summary["total_records"] == 20
    assert summary["latest_date"] == date(2025, 1, 20)
    assert summary["latest_close"] == pytest.approx(119.0)
    assert summary["latest_volume"] == 1019


@pytest.mark.skipif(
    sys.platform == "win32"
    and not (
        os.environ.get("HADOOP_HOME")
        and (
            Path(os.environ["HADOOP_HOME"])
            / "bin"
            / "winutils.exe"
        ).is_file()
    ),
    reason="Local Parquet writes on Windows require Hadoop winutils.exe",
)
def test_run_gold_persists_both_gold_datasets(
    spark, bronze_schema, tmp_path
):
    rows = [
        (
            "2025-01-01", 99.0, 100.0, 102.0, 98.0, 99.0,
            1000, "AAPL", "2025-01-02T10:00:00+00:00", "yahoo_finance",
        ),
        (
            "2025-01-02", 100.0, 101.0, 103.0, 99.0, 100.0,
            1100, "AAPL", "2025-01-03T10:00:00+00:00", "yahoo_finance",
        ),
    ]
    silver_dir = tmp_path / "silver"
    gold_dir = tmp_path / "gold"

    silver_df = transform_silver(
        spark.createDataFrame(rows, schema=bronze_schema)
    )
    silver_df.write.mode("overwrite").parquet(str(silver_dir))

    daily_gold_df, summary_df = run_gold(
        spark, silver_dir, gold_dir
    )

    assert daily_gold_df.count() == 2
    assert summary_df.count() == 1
    assert (
        spark.read.parquet(str(gold_dir / "daily_performance")).count()
        == 2
    )
    assert (
        spark.read.parquet(str(gold_dir / "ticker_summary")).count()
        == 1
    )
