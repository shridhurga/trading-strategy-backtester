import pandas as pd

from backtest.engine import run_backtest, _slim_metrics


def split_walk_forward(start: str, end: str, train_ratio: float = 0.7) -> tuple[str, str, str, str]:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    split_ts = start_ts + (end_ts - start_ts) * train_ratio
    split = split_ts.strftime("%Y-%m-%d")
    return start, split, split, end


def run_walk_forward(strategy_code: str, ticker: str, start: str, end: str,
                     initial_cash: float = 100_000, train_ratio: float = 0.7) -> dict:
    in_start, in_end, out_start, out_end = split_walk_forward(start, end, train_ratio)

    in_metrics = run_backtest(strategy_code, ticker, in_start, in_end, initial_cash)
    out_metrics = run_backtest(strategy_code, ticker, out_start, out_end, initial_cash)

    decay = round(out_metrics["total_return"] - in_metrics["total_return"], 2)
    if decay < -15:
        verdict = "High overfitting risk — out-of-sample return is much weaker."
    elif decay < -5:
        verdict = "Moderate decay — strategy may not generalize fully."
    else:
        verdict = "Reasonable generalization — out-of-sample performance is stable."

    return {
        "train_ratio": train_ratio,
        "in_sample": _slim_metrics(in_metrics),
        "out_of_sample": _slim_metrics(out_metrics),
        "return_decay": decay,
        "verdict": verdict,
        "in_sample_full": in_metrics,
        "out_of_sample_full": out_metrics,
    }
