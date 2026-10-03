from backtest.engine import run_backtest, _slim_metrics


def compare_strategies(runs: list[dict]) -> dict:
    """Compare multiple {name, code, ticker, start, end, cash} entries."""
    results = []
    for run in runs:
        metrics = run_backtest(
            run["code"], run["ticker"], run["start"], run["end"], run["cash"]
        )
        results.append({
            "name": run["name"],
            "metrics": _slim_metrics(metrics),
            "equity_dates": metrics["equity_dates"],
            "equity_values": metrics["equity_values"],
        })

    ranked = sorted(results, key=lambda r: r["metrics"]["total_return"], reverse=True)
    return {"results": results, "best": ranked[0]["name"] if ranked else None}
