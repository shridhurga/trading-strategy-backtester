import pandas as pd

from backtest.data import add_indicators


def test_add_indicators_creates_expected_columns():
    dates = pd.date_range("2023-01-01", periods=260, freq="D")
    frame = pd.DataFrame(
        {
            "Open": range(100, 360),
            "High": range(101, 361),
            "Low": range(99, 359),
            "Close": range(100, 360),
            "Volume": [1000] * 260,
        },
        index=dates,
    )

    result = add_indicators(frame)

    assert not result.empty
    assert {"SMA_50", "SMA_200", "RSI", "MACD", "MACD_SIG"}.issubset(result.columns)
    assert result["SMA_50"].notna().all()
    assert result["SMA_200"].notna().all()
