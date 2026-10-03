#!/usr/bin/env python3
"""CLI for AI Trading Strategy Backtester."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DEFAULT_CASH, DEFAULT_END, DEFAULT_START, DEFAULT_TICKER


def cmd_run(args):
    from core.pipeline import run_full_pipeline

    metrics_only = run_full_pipeline(
        args.strategy, args.ticker or DEFAULT_TICKER,
        args.start or DEFAULT_START, args.end or DEFAULT_END,
        args.cash or DEFAULT_CASH, demo_mode=args.demo,
    )
    _, _, metrics, narrative, _, _, is_demo = metrics_only
    slim = {k: v for k, v in metrics.items()
            if k not in ("equity_dates", "equity_values", "trade_log")}
    print(json.dumps(slim, indent=2))
    if is_demo:
        print("\n(Demo mode — no API used)")
    if args.report:
        print("\nReport:\n", narrative)


def cmd_walk(args):
    from backtest.walk_forward import run_walk_forward
    from core.pipeline import resolve_strategy

    spec, code, _ = resolve_strategy(
        args.strategy, args.ticker or DEFAULT_TICKER,
        args.start or DEFAULT_START, args.end or DEFAULT_END, args.demo,
    )
    wf = run_walk_forward(code, spec["ticker"], spec["start"], spec["end"],
                          args.cash or DEFAULT_CASH, args.train_ratio)
    print(json.dumps({k: v for k, v in wf.items() if not k.endswith("_full")}, indent=2))


def cmd_ui(_args):
    import subprocess
    subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/app.py"])


def main():
    p = argparse.ArgumentParser(description="AI Trading Strategy Backtester")
    sub = p.add_subparsers(dest="cmd")

    run = sub.add_parser("run", help="Run a single backtest")
    run.add_argument("strategy")
    run.add_argument("--ticker", default=None)
    run.add_argument("--start", default=None)
    run.add_argument("--end", default=None)
    run.add_argument("--cash", type=float, default=None)
    run.add_argument("--demo", action="store_true")
    run.add_argument("--report", action="store_true")

    walk = sub.add_parser("walk", help="Walk-forward validation")
    walk.add_argument("strategy")
    walk.add_argument("--ticker", default=None)
    walk.add_argument("--start", default=None)
    walk.add_argument("--end", default=None)
    walk.add_argument("--cash", type=float, default=None)
    walk.add_argument("--train-ratio", type=float, default=0.7)
    walk.add_argument("--demo", action="store_true")

    sub.add_parser("ui", help="Launch Streamlit app")

    args = p.parse_args()
    if args.cmd == "run":
        cmd_run(args)
    elif args.cmd == "walk":
        cmd_walk(args)
    elif args.cmd == "ui":
        cmd_ui(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
