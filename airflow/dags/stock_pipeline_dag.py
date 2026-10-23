"""Airflow orchestration for the stock market analytics pipeline.

Airflow is intended to run in Linux or WSL2. The project commands can run in
their own virtual environment by setting STOCK_PIPELINE_PYTHON and making the
dbt executable available as STOCK_PIPELINE_DBT.
"""

from __future__ import annotations

import os
import shlex
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Airflow is installed in the separate Linux/WSL orchestration environment,
# not in the project's Windows development environment.
from airflow.providers.standard.operators.bash import BashOperator  # pyright: ignore[reportMissingImports]
from airflow.sdk import DAG  # pyright: ignore[reportMissingImports]


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_PYTHON = os.environ.get("STOCK_PIPELINE_PYTHON", sys.executable)
DBT_EXECUTABLE = os.environ.get("STOCK_PIPELINE_DBT", "dbt")
DBT_PROJECT = PROJECT_ROOT / "dbt" / "stock_analytics"
TASK_ENV = {
    "PYTHONPATH": os.pathsep.join(
        (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT / "spark"))
    )
}


with DAG(
    dag_id="stock_market_data_pipeline",
    description="Extract, process, load, and build stock market analytics.",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    schedule="0 23 * * 1-5",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "stock_pipeline",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["stocks", "analytics"],
) as dag:
    extract_to_bronze = BashOperator(
        task_id="extract_transform_validate_to_bronze",
        bash_command=f"{shlex.quote(PROJECT_PYTHON)} pipeline.py",
        cwd=str(PROJECT_ROOT),
        env=TASK_ENV,
        append_env=True,
    )

    build_silver_gold = BashOperator(
        task_id="build_silver_and_gold",
        bash_command=f"{shlex.quote(PROJECT_PYTHON)} spark/run_pipeline.py",
        cwd=str(PROJECT_ROOT),
        env=TASK_ENV,
        append_env=True,
    )

    load_postgres = BashOperator(
        task_id="load_postgres_warehouse",
        bash_command=f"{shlex.quote(PROJECT_PYTHON)} spark/load_postgres.py",
        cwd=str(PROJECT_ROOT),
        env=TASK_ENV,
        append_env=True,
    )

    build_dbt_analytics = BashOperator(
        task_id="build_and_test_dbt_analytics",
        bash_command=(
            '"${STOCK_PIPELINE_DBT:-'
            + shlex.quote(DBT_EXECUTABLE)
            + '}" build --project-dir '
            + shlex.quote(str(DBT_PROJECT))
            + ' --profiles-dir "${DBT_PROFILES_DIR:-$HOME/.dbt}"'
        ),
        cwd=str(PROJECT_ROOT),
        env=TASK_ENV,
        append_env=True,
    )

    extract_to_bronze.set_downstream(build_silver_gold)
    build_silver_gold.set_downstream(load_postgres)
    load_postgres.set_downstream(build_dbt_analytics)
