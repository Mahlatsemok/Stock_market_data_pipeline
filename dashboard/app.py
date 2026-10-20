"""Streamlit dashboard for the PostgreSQL Gold stock datasets."""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import SupportsFloat

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


st.set_page_config(
    page_title="Stock Market Analytics",
    page_icon="📈",
    layout="wide",
)


@st.cache_resource
def get_engine(database_url: str) -> Engine:
    """Create one reusable SQLAlchemy engine for this dashboard process."""
    return create_engine(database_url, pool_pre_ping=True)


@st.cache_data(ttl=300)
def load_ticker_summary(database_url: str) -> pd.DataFrame:
    query = text(
        """
        SELECT ticker, total_records, first_date, last_date, latest_date,
               latest_close, latest_volume, highest_close, lowest_close,
               average_close, average_volume, best_daily_return,
               worst_daily_return, average_daily_return, volatility
        FROM ticker_summary
        ORDER BY ticker
        """
    )
    with get_engine(database_url).connect() as connection:
        return pd.read_sql_query(query, connection)


@st.cache_data(ttl=300)
def load_daily_data(
    database_url: str,
    ticker: str,
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    query = text(
        """
        SELECT ticker, date, open, high, low, close, volume,
               daily_return, ma5, ma20
        FROM daily_performance
        WHERE ticker = :ticker AND date BETWEEN :start_date AND :end_date
        ORDER BY date
        """
    )
    with get_engine(database_url).connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
            params={
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
            },
            parse_dates=["date"],
        )


def format_number(value: SupportsFloat | None, decimals: int = 2) -> str:
    if value is None:
        return "—"
    number = float(value)
    if pd.isna(number):
        return "—"
    return f"{number:,.{decimals}f}"


def main() -> None:
    st.title("📈 Stock Market Analytics")
    st.caption("Gold layer performance data from the PostgreSQL warehouse")

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        st.info(
            "Set the DATABASE_URL environment variable, then load the Phase 5 "
            "Gold datasets into PostgreSQL to view the dashboard. See the "
            "README for setup instructions."
        )
        st.stop()

    try:
        summary = load_ticker_summary(database_url)
    except Exception:
        st.error(
            "Could not read the PostgreSQL warehouse. Confirm the database is "
            "running and the Gold tables have been loaded."
        )
        st.stop()

    if summary.empty:
        st.warning("The ticker_summary table has no rows. Run the pipeline and load Gold data first.")
        st.stop()

    ticker_options = summary["ticker"].astype(str).tolist()
    with st.sidebar:
        st.header("Explore")
        ticker = st.selectbox("Ticker", ticker_options)
        selected_summary = summary.loc[summary["ticker"] == ticker].iloc[0]
        first_date = pd.Timestamp(selected_summary["first_date"]).date()
        last_date = pd.Timestamp(selected_summary["last_date"]).date()
        default_start = max(first_date, last_date - timedelta(days=365))
        selected_dates = st.date_input(
            "Date range",
            value=(default_start, last_date),
            min_value=first_date,
            max_value=last_date,
        )
        st.caption("Warehouse data refreshes every five minutes.")

    if isinstance(selected_dates, tuple):
        if len(selected_dates) != 2:
            st.info("Choose both a start and end date to display the price history.")
            start_date, end_date = None, None
        else:
            start_date, end_date = selected_dates
    else:
        start_date, end_date = selected_dates, selected_dates

    st.subheader(f"{ticker} performance")
    metric_columns = st.columns(4)
    metric_columns[0].metric("Latest close", f"${format_number(selected_summary['latest_close'])}")
    metric_columns[1].metric("Latest volume", format_number(selected_summary["latest_volume"], 0))
    metric_columns[2].metric("Records", format_number(selected_summary["total_records"], 0))
    metric_columns[3].metric(
        "Average daily return",
        f"{format_number(selected_summary['average_daily_return'])}%"
        if pd.notna(selected_summary["average_daily_return"])
        else "—",
    )

    st.caption(
        f"Data available from {first_date:%b %d, %Y} to {last_date:%b %d, %Y}. "
        f"All-time high: ${format_number(selected_summary['highest_close'])} · "
        f"All-time low: ${format_number(selected_summary['lowest_close'])}"
    )

    if start_date is None or end_date is None:
        daily = pd.DataFrame()
    else:
        try:
            daily = load_daily_data(database_url, ticker, start_date, end_date)
        except Exception:
            st.error("Could not read daily_performance from the warehouse.")
            st.stop()

    if daily.empty:
        st.info("No daily records are available for this ticker and date range.")
    else:
        prices = go.Figure()
        prices.add_trace(
            go.Scatter(x=daily["date"], y=daily["close"], name="Close", mode="lines")
        )
        prices.add_trace(
            go.Scatter(x=daily["date"], y=daily["ma5"], name="5-day average", mode="lines")
        )
        prices.add_trace(
            go.Scatter(x=daily["date"], y=daily["ma20"], name="20-day average", mode="lines")
        )
        prices.update_layout(
            title="Closing price and moving averages",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            hovermode="x unified",
            legend_title_text="Series",
            margin={"t": 55, "b": 20},
        )
        st.plotly_chart(
            prices,
            width="stretch",
            alt=f"{ticker} daily closing price with 5-day and 20-day moving averages.",
        )

        return_column, volume_column = st.columns(2)
        returns = go.Figure(
            go.Bar(
                x=daily["date"],
                y=daily["daily_return"],
                marker_color=[
                    "#16a34a" if pd.notna(value) and value >= 0 else "#dc2626"
                    for value in daily["daily_return"]
                ],
                name="Daily return",
            )
        )
        returns.update_layout(
            title="Daily return",
            xaxis_title="Date",
            yaxis_title="Return (%)",
            margin={"t": 55, "b": 20},
        )
        return_column.plotly_chart(
            returns,
            width="stretch",
            alt=f"{ticker} daily percentage returns for the selected date range.",
        )

        volumes = go.Figure(
            go.Bar(x=daily["date"], y=daily["volume"], marker_color="#2563eb", name="Volume")
        )
        volumes.update_layout(
            title="Daily trading volume",
            xaxis_title="Date",
            yaxis_title="Shares",
            margin={"t": 55, "b": 20},
        )
        volume_column.plotly_chart(
            volumes,
            width="stretch",
            alt=f"{ticker} daily trading volume for the selected date range.",
        )

    st.subheader("Ticker comparison")
    comparison_columns = [
        "ticker",
        "latest_date",
        "latest_close",
        "total_records",
        "average_daily_return",
        "volatility",
        "highest_close",
        "lowest_close",
    ]
    st.dataframe(
        summary[comparison_columns].rename(
            columns={
                "ticker": "Ticker",
                "latest_date": "Latest date",
                "latest_close": "Latest close",
                "total_records": "Records",
                "average_daily_return": "Average return",
                "volatility": "Volatility",
                "highest_close": "Highest close",
                "lowest_close": "Lowest close",
            }
        ),
        hide_index=True,
        alt="Summary comparison of the available stock tickers and their performance metrics.",
    )


if __name__ == "__main__":
    main()
