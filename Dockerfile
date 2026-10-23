# syntax=docker/dockerfile:1.7
FROM apache/spark:4.2.0-java17 AS spark-runtime

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    SPARK_HOME=/opt/spark \
    STOCK_PIPELINE_ROOT=/app \
    PYTHONPATH=/opt/spark/python \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

COPY --from=spark-runtime /opt/spark /opt/spark
COPY pyproject.toml README.md ./
COPY src ./src
COPY spark ./spark
COPY dashboard ./dashboard
COPY pipeline.py ./pipeline.py
COPY config ./config
COPY sql ./sql
COPY dbt/stock_analytics ./dbt/stock_analytics
COPY docker/entrypoint.sh /usr/local/bin/stock-pipeline-entrypoint

RUN --mount=type=cache,target=/root/.cache/pip,id=stock-market-pip-cache-v2 \
    python -m pip install ".[postgres,dbt,dashboard]" \
    && addgroup --system stockapp \
    && adduser --system --ingroup stockapp --home /home/stockapp stockapp \
    && mkdir -p /home/stockapp/.dbt /app/data /app/logs \
    && cp dbt/stock_analytics/profiles.yml.example /home/stockapp/.dbt/profiles.yml \
    && chown -R stockapp:stockapp /app /home/stockapp \
    && chmod +x /usr/local/bin/stock-pipeline-entrypoint

USER stockapp
ENTRYPOINT ["/usr/local/bin/stock-pipeline-entrypoint"]
