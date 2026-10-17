from datetime import date, datetime, timezone
import os
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

from stock_processing import transform_silver


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
