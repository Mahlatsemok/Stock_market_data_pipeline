#!/bin/sh
set -eu

PY4J_ZIP="$(find /opt/spark/python/lib -maxdepth 1 -name 'py4j-*.zip' -print -quit)"
if [ -z "$PY4J_ZIP" ]; then
    echo "Could not find the Py4J library bundled with Spark." >&2
    exit 1
fi
export PYTHONPATH="/opt/spark/python:$PY4J_ZIP${PYTHONPATH:+:$PYTHONPATH}"

export DATABASE_URL="$(python -c 'import os; from sqlalchemy.engine import URL; print(URL.create("postgresql+psycopg", username=os.environ["POSTGRES_USER"], password=os.environ["POSTGRES_PASSWORD"], host=os.environ.get("POSTGRES_HOST", "postgres"), port=int(os.environ.get("POSTGRES_PORT", "5432")), database=os.environ["POSTGRES_DB"]).render_as_string(hide_password=False))')"
export DBT_HOST="${POSTGRES_HOST:-postgres}"
export DBT_PORT="${POSTGRES_PORT:-5432}"
export DBT_USER="$POSTGRES_USER"
export DBT_DATABASE="$POSTGRES_DB"
export DBT_SCHEMA="${DBT_SCHEMA:-public}"
export DBT_SOURCE_SCHEMA="${DBT_SOURCE_SCHEMA:-public}"
export DBT_ENV_SECRET_PASSWORD="$POSTGRES_PASSWORD"
export DBT_PROFILES_DIR="${DBT_PROFILES_DIR:-/home/stockapp/.dbt}"

exec "$@"
