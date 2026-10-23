# Stock Market Data Pipeline

A Python project for collecting daily stock prices, validating and transforming the data, and building a path toward an analytics warehouse.

## Current project status

The repository contains an end-to-end stock data pipeline with Bronze ingestion, Spark Silver and Gold processing, a PostgreSQL warehouse, dbt analytics, automated tests, a Streamlit dashboard, an Airflow DAG, and a Docker Compose runtime. See the implementation roadmap below for the project phases.

## Requirements

- Python 3.11 or newer
- Internet access when downloading market data from Yahoo Finance
- PostgreSQL for the warehouse load step (optional for the local CSV pipeline)
- Java and PySpark for the Spark processing step (optional for the local CSV pipeline)

## Setup

From the repository root, create and activate a virtual environment, then install the package and development dependencies:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,spark]"
```

Alternatively, install the pinned runtime packages with `python -m pip install -r requirements.txt`. The editable install is preferred for development because it makes the `stock_pipeline` package available directly from `src/`.

## Configuration

Edit `config/stocks.yaml` to choose the ticker symbols. The pipeline reads that file and uses Yahoo Finance as its source. Do not commit credentials or local secrets; put local settings in `.env` when environment-based settings are added.

## Run the local pipeline

```powershell
python pipeline.py
```

The pipeline downloads up to ten years of daily data for each configured symbol, transforms and validates each ticker, writes per-ticker files under `data/raw/` and `data/processed/`, combines successful records under `data/combined/`, and records failures under `data/quarantine/`.

Extraction validates ticker symbols before using them in requests or output paths, requests one ticker at a time with a 30-second timeout, and retries failed or incomplete responses up to three times by default. The delay between retries is configurable through the extractor's `retry_delay` argument.

Each successful extraction is also saved as an immutable, timestamped CSV snapshot in `data/bronze/` with its source and UTC ingestion time. The transform step quarantines invalid rows with a reason, checks dates, finite numeric values, whole-number non-negative volume, positive prices, and consistent OHLC ranges, then writes clean records to `data/processed/`. When a date has both malformed and valid duplicates, it keeps the first valid record and quarantines the malformed row.

## Run Spark Silver and Gold

Install Java and the Spark extra using the setup command above, then run:

```powershell
python spark/run_pipeline.py
```

The job reads Bronze CSV snapshots from `data/bronze/`, writes validated and deduplicated Silver Parquet data to `data/silver/`, and writes two Gold Parquet datasets under `data/gold/`: `daily_performance/` contains daily returns, five- and twenty-day moving averages, and calendar fields; `ticker_summary/` contains one aggregated performance row per ticker. Use `--bronze-dir`, `--silver-dir`, or `--gold-dir` to override the paths.

On Windows, local Spark file writes also require Hadoop's `winutils.exe`. Install a Hadoop Windows utilities build, then set `HADOOP_HOME` to the directory containing its `bin/winutils.exe`; Apache's [Windows troubleshooting guide](https://cwiki.apache.org/confluence/display/HADOOP2/WindowsProblems) describes this requirement.

## Load Gold data into PostgreSQL

Install and start PostgreSQL, create a database and user for the project, then install the PostgreSQL driver:

```powershell
python -m pip install -e ".[postgres]"
```

Set `DATABASE_URL` in the current PowerShell session. Replace the example user, password, host, and database with your local PostgreSQL settings; do not commit real credentials:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://stock_user:your_password@localhost:5432/stock_market"
```

Run the Spark job first if the Gold Parquet datasets do not already exist, then load them:

```powershell
python spark/run_pipeline.py
python spark/load_postgres.py
```

The loader creates the tables and indexes from `sql/schema.sql` when needed. It loads `data/gold/daily_performance/` into `daily_performance` and `data/gold/ticker_summary/` into `ticker_summary`. Re-running the load updates matching ticker/date keys instead of inserting duplicate rows. `DATABASE_URL` is read from the process environment; `.env.example` documents its expected format.

Run the sample warehouse queries in `sql/queries.sql` after the load.

## Build dbt analytics models

Phase 6 uses dbt Core with the PostgreSQL adapter. Install the optional dbt dependencies:

```powershell
python -m pip install -e ".[dbt]"
```

Copy the safe profile template to your user-level dbt configuration directory, then set the connection variables in PowerShell. The database and source schema should match the PostgreSQL settings used in Phase 5:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.dbt"
Copy-Item dbt\stock_analytics\profiles.yml.example "$env:USERPROFILE\.dbt\profiles.yml"
$env:DBT_HOST = "localhost"
$env:DBT_PORT = "5432"
$env:DBT_USER = "stock_user"
$env:DBT_ENV_SECRET_PASSWORD = "your_password"
$env:DBT_DATABASE = "stock_market"
$env:DBT_SCHEMA = "public"
$env:DBT_SOURCE_SCHEMA = "public"
```

Check the profile connection and build the models and data tests:

```powershell
dbt debug --project-dir dbt\stock_analytics --profiles-dir "$env:USERPROFILE\.dbt"
dbt build --project-dir dbt\stock_analytics --profiles-dir "$env:USERPROFILE\.dbt"
```

The models read the Phase 5 `daily_performance` and `ticker_summary` source tables. Staging views are created in `dbt_staging`; the daily fact, ticker dimension, and monthly performance table are created in `dbt_analytics`. The project includes source, column, and grain/count checks. Keep your real `profiles.yml` and password out of Git.

## Run the Streamlit dashboard

The dashboard reads the PostgreSQL Gold tables created in Phase 5. Install its optional dependencies and configure the same `DATABASE_URL` used by the warehouse loader:

```powershell
python -m pip install -e ".[dashboard]"
$env:DATABASE_URL = "postgresql+psycopg://stock_user:YOUR_REAL_PASSWORD@localhost:5432/stock_market"
streamlit run dashboard/app.py
```

Load the Gold datasets into PostgreSQL before opening the dashboard. It provides ticker and date filters, daily close and moving-average charts, daily return and volume charts, key performance metrics, and a ticker comparison table. Database credentials are read from the environment and must not be committed.

## Run with Docker Compose (Phase 10)

Docker Compose starts PostgreSQL and the Streamlit dashboard. The optional
`pipeline` service runs extraction, Spark Silver and Gold processing, the
PostgreSQL load, and `dbt build` in sequence. Generated data, the database,
and pipeline logs are persisted in named Docker volumes.

From PowerShell, copy the example environment file and replace the sample
database password with a private value:

```powershell
Copy-Item .env.example .env
```

Run the complete pipeline once (the first build downloads the Apache Spark
runtime and installs the Python, PostgreSQL, dbt, and dashboard dependencies):

```powershell
docker compose --profile pipeline run --build --rm pipeline
```

After it finishes successfully, start the dashboard:

```powershell
docker compose up --build -d dashboard
```

Open <http://localhost:8501>. To inspect service status and dashboard output,
use `docker compose ps` and `docker compose logs -f dashboard`. Stop the
services with `docker compose down`; this keeps the database, pipeline data,
and logs volumes. The Airflow installation described in Phase 9 remains a
separate WSL2 service.

## Run tests

```powershell
python -m pytest
```

GitHub Actions runs this suite on pushes, pull requests, and manual runs using Python 3.11 and 3.14. The workflow installs the project with its development and Spark dependencies and sets up Java for the Spark tests. Review the **Tests** check on the Actions tab after pushing a change.

## Repository layout

```text
config/                 Ticker configuration
src/stock_pipeline/     Extraction, Bronze, transforms, quality, and loading code
spark/                  Bronze-to-Silver Spark processing
sql/                    Warehouse schema and analysis queries
tests/                  Automated tests
dbt/                    dbt PostgreSQL staging views, marts, and data tests
dashboard/              Streamlit dashboard
airflow/dags/           Airflow orchestration DAG
docker/                 Docker container entrypoint
data/                   Local pipeline outputs; treat these as generated data
```

## Implementation roadmap

Work through the phases in order, completing and reviewing each phase before moving on:

1. Repository and foundation
2. Reliable extraction
3. Data quality and Bronze
4. Spark Silver and Gold
5. PostgreSQL warehouse
6. dbt analytics models
7. Automated testing
8. Streamlit dashboard
9. Airflow orchestration
10. Docker and final release

## Airflow orchestration (Phase 9)

The `stock_market_data_pipeline` DAG runs the existing stages in order:

1. Extract, transform, validate, and write Bronze data with `pipeline.py`.
2. Build Silver and Gold datasets with Spark.
3. Load the Gold datasets into PostgreSQL.
4. Run `dbt build` to build and test analytics models.

Airflow does not run natively on Windows. Use WSL2 (or another Linux host) for
the Airflow installation, and keep it in a separate virtual environment from
the project so Airflow's dependency constraints do not conflict with Spark,
dbt, or the dashboard. Install the project dependencies in the project's own
Linux virtual environment, then configure Airflow to invoke that environment:

```bash
export STOCK_PIPELINE_PYTHON="/path/to/project-venv/bin/python"
export STOCK_PIPELINE_DBT="/path/to/project-venv/bin/dbt"
export AIRFLOW_HOME="$HOME/airflow"
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/airflow/dags"
export DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST:5432/stock_market"
export DBT_PROFILES_DIR="$HOME/.dbt"
```

Create the Airflow environment and install Airflow with the matching official
constraints file for your Python version. Install the Standard provider too;
the DAG uses its `BashOperator`. Initialize Airflow with `airflow standalone`,
then enable and trigger `stock_market_data_pipeline` in the Airflow UI. The
schedule is weekdays at 23:00 UTC. Ensure `DATABASE_URL` points to a PostgreSQL
server reachable from WSL2, and configure the dbt profile in
`$DBT_PROFILES_DIR/profiles.yml`.

For Windows-specific installation guidance, use the [Airflow Quick Start](https://airflow.apache.org/docs/apache-airflow/stable/start.html)
and [BashOperator documentation](https://airflow.apache.org/docs/apache-airflow-providers-standard/stable/operators/bash.html).

## Data and credentials

Pipeline output files and local databases can be large or machine-specific. Avoid committing generated data, credentials, or `.env` files. The repository may contain existing local artifacts from development; review `git status` before committing changes.
