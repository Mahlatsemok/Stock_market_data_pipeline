from pathlib import Path

import yaml


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# DIRECTORIES
# ============================================================

DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

PROCESSED_DATA_DIR = DATA_DIR / "processed"

QUARANTINE_DIR = DATA_DIR / "quarantine"

CONFIG_DIR = PROJECT_ROOT / "config"

DATABASE_DIR = PROJECT_ROOT / "database"


# ============================================================
# CONFIGURATION
# ============================================================

STOCKS_CONFIG_FILE = (
    CONFIG_DIR / "stocks.yaml"
)


FAILED_TICKERS_FILE = (
    QUARANTINE_DIR / "failed_tickers.csv"
)


# ============================================================
# CREATE DIRECTORIES
# ============================================================

RAW_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

PROCESSED_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

QUARANTINE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD TICKERS
# ============================================================

def load_tickers():
    """
    Load stock tickers from stocks.yaml.
    """

    with open(
        STOCKS_CONFIG_FILE,
        "r"
    ) as file:

        config = yaml.safe_load(file)

    return config["stocks"]