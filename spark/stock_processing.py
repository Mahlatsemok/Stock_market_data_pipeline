import os
import sys
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


BRONZE_SCHEMA = StructType(
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


def create_spark_session(app_name: str = "stock-market-silver") -> SparkSession:
    """Create a local Spark session for stock data processing."""
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
    return (
        SparkSession.builder
        .appName(app_name)
        .master("local[2]")
        .config("spark.pyspark.python", sys.executable)
        .config("spark.pyspark.driver.python", sys.executable)
        .getOrCreate()
    )


def read_bronze(spark: SparkSession, bronze_dir: str | Path) -> DataFrame:
    """Read Bronze CSV snapshots using explicit file paths."""
    bronze_path = Path(bronze_dir)

    if not bronze_path.is_dir():
        raise FileNotFoundError(
            f"Bronze directory does not exist: {bronze_path}"
        )

    csv_files = sorted(
        str(file.resolve())
        for file in bronze_path.glob("*.csv")
        if file.is_file()
    )

    if not csv_files:
        raise FileNotFoundError(
            f"No Bronze CSV files found in: {bronze_path}"
        )

    return (
        spark.read
        .option("header", True)
        .option("mode", "PERMISSIVE")
        .schema(BRONZE_SCHEMA)
        .csv(csv_files)
    )


def transform_silver(bronze_df: DataFrame) -> DataFrame:
    """Standardize, validate, and deduplicate Bronze stock records."""
    df = bronze_df.withColumn(
        "Date", F.to_date(F.col("Date"), "yyyy-MM-dd")
    )

    df = (
        df.withColumn("Ticker", F.upper(F.trim(F.col("Ticker"))))
        .withColumn("source_system", F.trim(F.col("source_system")))
        .withColumn(
            "ingested_at_utc",
            F.to_timestamp(F.col("ingested_at_utc")),
        )
    )

    required_columns = [
        "Date",
        "Ticker",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "ingested_at_utc",
        "source_system",
    ]

    valid_condition = F.lit(True)
    for column in required_columns:
        valid_condition = valid_condition & F.col(column).isNotNull()

    for column in ["Open", "High", "Low", "Close"]:
        valid_condition = (
            valid_condition
            & (~F.isnan(F.col(column)))
            & (F.abs(F.col(column)) != F.lit(float("inf")))
            & (F.col(column) > 0)
        )

    valid_condition = (
        valid_condition
        & (F.col("Volume") >= 0)
        & (~F.isnan(F.col("Volume").cast("double")))
        & (F.abs(F.col("Volume").cast("double")) != F.lit(float("inf")))
        & (F.col("High") >= F.col("Low"))
        & (F.col("High") >= F.col("Open"))
        & (F.col("High") >= F.col("Close"))
        & (F.col("Low") <= F.col("Open"))
        & (F.col("Low") <= F.col("Close"))
        & (F.length(F.col("Ticker")) > 0)
        & (F.length(F.col("source_system")) > 0)
    )

    df = df.filter(valid_condition)

    # Keep the most recently ingested copy of each ticker/date record.
    window = Window.partitionBy("Ticker", "Date").orderBy(
        F.col("ingested_at_utc").desc(),
        F.col("source_system").asc(),
    )

    df = (
        df.withColumn("_record_rank", F.row_number().over(window))
        .filter(F.col("_record_rank") == 1)
        .drop("_record_rank")
    )

    # Put the key business columns first and preserve optional adjusted close.
    columns = [
        "Date",
        "Ticker",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]
    if "Adj Close" in df.columns:
        columns.append("Adj Close")
    columns.extend(["ingested_at_utc", "source_system"])

    return df.select(*columns)


def write_silver(silver_df: DataFrame, output_dir: str | Path) -> None:
    """Write the Silver dataset in Parquet format."""
    (
        silver_df.write
        .mode("overwrite")
        .parquet(str(output_dir))
    )


def run_silver(
    spark: SparkSession,
    bronze_dir: str | Path,
    output_dir: str | Path,
) -> DataFrame:
    """Run the Bronze-to-Silver transformation and persist its output."""
    bronze_df = read_bronze(spark, bronze_dir)
    silver_df = transform_silver(bronze_df)
    write_silver(silver_df, output_dir)
    return silver_df
