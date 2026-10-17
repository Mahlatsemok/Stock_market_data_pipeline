import argparse
from pathlib import Path

from stock_processing import create_spark_session, run_gold, run_silver


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Silver and Gold stock datasets from Bronze CSVs."
    )
    parser.add_argument(
        "--bronze-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "bronze",
    )
    parser.add_argument(
        "--silver-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "silver",
    )
    parser.add_argument(
        "--gold-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "gold",
    )
    args = parser.parse_args()

    spark = create_spark_session("stock-market-silver-gold")
    try:
        run_silver(spark, args.bronze_dir, args.silver_dir)
        run_gold(spark, args.silver_dir, args.gold_dir)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
