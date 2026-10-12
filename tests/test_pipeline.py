import pandas as pd

import pipeline


def test_successful_run_clears_stale_failed_ticker_report(
    tmp_path, monkeypatch
):
    failed_report = tmp_path / "failed_tickers.csv"
    combined_dir = tmp_path / "combined"

    failed_report.write_text(
        "Ticker,Reason\nOLD,Previous failure\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        pipeline, "FAILED_TICKERS_FILE", failed_report
    )
    monkeypatch.setattr(
        pipeline, "COMBINED_DATA_DIR", combined_dir
    )
    monkeypatch.setattr(
        pipeline, "load_tickers", lambda: ["AAPL"]
    )
    monkeypatch.setattr(
        pipeline, "setup_logging", lambda: None
    )
    monkeypatch.setattr(
        pipeline,
        "extract_stock_data",
        lambda ticker, period: pd.DataFrame(
            {
                "Date": pd.to_datetime(["2025-01-01"]),
                "Open": [100.0],
                "High": [102.0],
                "Low": [99.0],
                "Close": [101.0],
                "Volume": [1000],
            }
        ),
    )

    valid_data = pd.DataFrame(
        {
            "Ticker": ["AAPL"],
            "Date": pd.to_datetime(["2025-01-01"]),
            "Open": [100.0],
            "High": [102.0],
            "Low": [99.0],
            "Close": [101.0],
            "Volume": [1000],
        }
    )

    monkeypatch.setattr(
        pipeline,
        "transform_stock_data",
        lambda df, ticker: valid_data.copy(),
    )
    monkeypatch.setattr(
        pipeline, "validate_stock_data", lambda df, ticker: None
    )

    pipeline.main()

    report = pd.read_csv(failed_report)

    assert list(report.columns) == ["Ticker", "Reason"]
    assert report.empty


def test_failed_report_is_saved_when_all_extractions_fail(
    tmp_path, monkeypatch
):
    failed_report = tmp_path / "failed_tickers.csv"

    monkeypatch.setattr(
        pipeline, "FAILED_TICKERS_FILE", failed_report
    )
    monkeypatch.setattr(
        pipeline, "COMBINED_DATA_DIR", tmp_path / "combined"
    )
    monkeypatch.setattr(
        pipeline, "load_tickers", lambda: ["AAPL", "MSFT"]
    )
    monkeypatch.setattr(
        pipeline, "setup_logging", lambda: None
    )
    monkeypatch.setattr(
        pipeline,
        "extract_stock_data",
        lambda ticker, period: pd.DataFrame(),
    )

    pipeline.main()

    report = pd.read_csv(failed_report)

    assert report["Ticker"].tolist() == ["AAPL", "MSFT"]
    assert report["Reason"].eq("No data returned").all()
    