"""Load the Spark Gold Parquet datasets into PostgreSQL."""

import argparse
import os
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from stock_pipeline.load.postgres import load_gold_to_postgres  # noqa: E402
from stock_processing import create_spark_session  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load Gold Parquet datasets into PostgreSQL."
    )
    parser.add_argument(
        "--gold-dir",
        type=Path,
        default=REPOSITORY_ROOT / "data" / "gold",
        help="Directory containing daily_performance/ and ticker_summary/.",
    )
    args = parser.parse_args()

    connection_string = os.environ.get("DATABASE_URL")
    if not connection_string:
        raise SystemExit(
            "DATABASE_URL is not set. Set it to your PostgreSQL connection "
            "URL, for example postgresql+psycopg://user:password@localhost:5432/stocks."
        )

    daily_path = args.gold_dir / "daily_performance"
    summary_path = args.gold_dir / "ticker_summary"
    for path in (daily_path, summary_path):
        if not path.is_dir():
            raise FileNotFoundError(f"Gold dataset directory not found: {path}")

    spark = create_spark_session("stock-gold-to-postgres")
    try:
        daily_performance = spark.read.parquet(str(daily_path)).toPandas()
        ticker_summary = spark.read.parquet(str(summary_path)).toPandas()
    finally:
        spark.stop()

    daily_count, summary_count = load_gold_to_postgres(
        daily_performance,
        ticker_summary,
        connection_string,
    )
    print(
        "PostgreSQL load complete: "
        f"{daily_count:,} daily rows and {summary_count:,} ticker summaries."
    )


if __name__ == "__main__":
    main()
