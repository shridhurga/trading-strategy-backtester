import pandas as pd
import pytest

from backtest.data import add_indicators
from backtest.engine import _buy_hold_return, run_backtest
from backtest.walk_forward import split_walk_forward
from demo.fallback import DEMO_CODE


def _sample_df(n=260):
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    close = pd.Series(range(100, 100 + n), index=dates, dtype=float)
    return pd.DataFrame({
        "Open": close, "High": close + 1, "Low": close - 1,
        "Close": close, "Volume": 1000,
    })


def test_add_indicators_columns():
    df = add_indicators(_sample_df())
    assert {"SMA_50", "RSI", "MACD"}.issubset(df.columns)


def test_buy_hold_return_positive():
    assert _buy_hold_return(_sample_df(), 100_000) > 0


def test_walk_forward_split():
    a, b, c, d = split_walk_forward("2019-01-01", "2024-01-01", 0.7)
    assert a == "2019-01-01"
    assert b == c
    assert d == "2024-01-01"


@pytest.mark.integration
def test_demo_backtest_runs():
    metrics = run_backtest(DEMO_CODE, "^NSEI", "2020-01-01", "2021-01-01", 100_000)
    assert "total_return" in metrics
    assert metrics["total_trades"] >= 0
