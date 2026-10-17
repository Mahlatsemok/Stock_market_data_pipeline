# Stock Market Data Pipeline

A Python project for collecting daily stock prices, validating and transforming the data, and building a path toward an analytics warehouse.

## Current project status

The repository contains a working Python extraction and transformation pipeline, Bronze CSV ingestion, Spark Silver processing, PostgreSQL loading code, SQL, tests, and starter files for dbt, Streamlit, Airflow, and Docker. Several later-stage components are still being built. See the implementation roadmap below for the intended order.

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

## Run tests

```powershell
python -m pytest
```

## Repository layout

```text
config/                 Ticker configuration
src/stock_pipeline/     Extraction, Bronze, transforms, quality, and loading code
spark/                  Bronze-to-Silver Spark processing
sql/                    Warehouse schema and analysis queries
tests/                  Automated tests
dbt/                    dbt project (analytics models are a later roadmap step)
dashboard/              Streamlit dashboard (later roadmap step)
airflow/                Airflow DAG (later roadmap step)
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

## Data and credentials

Pipeline output files and local databases can be large or machine-specific. Avoid committing generated data, credentials, or `.env` files. The repository may contain existing local artifacts from development; review `git status` before committing changes.
