import json
from pathlib import Path

from config import OUTPUT_DIR


def resolve_strategy(description: str, ticker: str, start: str, end: str,
                     demo_mode: bool, cash: float = 100_000):
    if demo_mode:
        from demo.fallback import DEMO_CODE, DEMO_SPEC
        spec = {**DEMO_SPEC, "ticker": ticker, "start": start, "end": end}
        return spec, DEMO_CODE, True

    from strategy.strategy_parser import parse_strategy
    from codegen.code_generator import generate_with_retry
    from backtest.engine import run_backtest

    spec = parse_strategy(description)
    spec.update({"ticker": ticker, "start": start, "end": end})

    def _validate(code):
        run_backtest(code, ticker, start, end, cash)

    code = generate_with_retry(spec, run_fn=_validate)
    return spec, code, False


def run_full_pipeline(description, ticker, start, end, cash, demo_mode=False):
    from backtest.engine import run_backtest
    from reporting.charts import generate_narrative, plot_equity_curve, plot_price_chart
    from demo.fallback import DEMO_NARRATIVE

    spec, code, is_demo = resolve_strategy(description, ticker, start, end, demo_mode, cash)
    metrics = run_backtest(code, ticker, start, end, cash)

    if is_demo:
        narrative = DEMO_NARRATIVE
    else:
        narrative = generate_narrative(metrics, spec)

    equity_fig = plot_equity_curve(metrics)
    price_fig = plot_price_chart(ticker, start, end, metrics["trade_log"])

    card = {
        "description": description,
        "spec": spec,
        "metrics": {k: v for k, v in metrics.items()
                    if k not in ("equity_dates", "equity_values", "trade_log")},
        "demo_mode": is_demo,
    }
    (OUTPUT_DIR / "last_run.json").write_text(json.dumps(card, indent=2))

    return spec, code, metrics, narrative, equity_fig, price_fig, is_demo


def format_api_error(err: str) -> str | None:
    if "429" in err or "quota" in err.lower() or "ResourceExhausted" in err:
        return (
            "Gemini API rate limit reached. Wait 60 seconds, enable Demo Mode, "
            "or upgrade your API key."
        )
    if "GEMINI_API_KEY" in err or "API key" in err:
        return "Missing GEMINI_API_KEY in .env — or enable Demo Mode in the sidebar."
    return None
