import json

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backtest.data import fetch_data, add_indicators
from core.gemini import clean_llm_output, get_model


def plot_equity_curve(metrics: dict):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=metrics["equity_dates"], y=metrics["equity_values"],
        mode="lines", name="Strategy",
        line=dict(color="#378ADD", width=2),
        fill="tozeroy", fillcolor="rgba(55,138,221,0.08)",
    ))
    initial = metrics["initial_cash"]
    bh_final = initial * (1 + metrics["buy_hold_return"] / 100)
    fig.add_trace(go.Scatter(
        x=[metrics["equity_dates"][0], metrics["equity_dates"][-1]],
        y=[initial, bh_final],
        mode="lines", name="Buy & Hold",
        line=dict(color="#888888", width=2, dash="dash"),
    ))
    fig.update_layout(
        title=f"{metrics['ticker']} — Strategy vs Buy & Hold",
        xaxis_title="Date", yaxis_title="Portfolio Value (INR)",
        hovermode="x unified", height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def plot_comparison_equity(results: list[dict]):
    fig = go.Figure()
    colors = ["#378ADD", "#1D9E75", "#D85A30", "#7C3AED"]
    for i, r in enumerate(results):
        fig.add_trace(go.Scatter(
            x=r["equity_dates"], y=r["equity_values"],
            mode="lines", name=r["name"],
            line=dict(color=colors[i % len(colors)], width=2),
        ))
    fig.update_layout(
        title="Strategy Comparison — Equity Curves",
        xaxis_title="Date", yaxis_title="Portfolio Value (INR)",
        hovermode="x unified", height=420,
    )
    return fig


def _nearest_price(df: pd.DataFrame, date_str: str):
    ts = pd.Timestamp(date_str)
    idx = df.index[df.index.get_indexer([ts], method="nearest")[0]]
    return idx, df.loc[idx, "Close"]


def plot_price_chart(ticker: str, start: str, end: str, trade_log: list | None = None):
    df = fetch_data(ticker, start, end)
    df = add_indicators(df)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3], vertical_spacing=0.05)
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Price",
                             line=dict(color="#378ADD")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA_50"], name="SMA 50",
                             line=dict(dash="dot", color="#1D9E75")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA_200"], name="SMA 200",
                             line=dict(dash="dot", color="#D85A30")), row=1, col=1)

    if trade_log:
        bx, by, sx, sy = [], [], [], []
        for t in trade_log:
            idx, p = _nearest_price(df, t["entry_date"])
            bx.append(idx); by.append(p)
            idx, p = _nearest_price(df, t["exit_date"])
            sx.append(idx); sy.append(p)
        fig.add_trace(go.Scatter(x=bx, y=by, mode="markers", name="Buy",
                                 marker=dict(symbol="triangle-up", size=9, color="#1D9E75")), row=1, col=1)
        fig.add_trace(go.Scatter(x=sx, y=sy, mode="markers", name="Sell",
                                 marker=dict(symbol="triangle-down", size=9, color="#D85A30")), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                             line=dict(color="#7C3AED")), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="#D85A30", row=2, col=1)
    fig.update_layout(title=f"{ticker} — Price & RSI", height=520, hovermode="x unified")
    return fig


def generate_narrative(metrics: dict, spec: dict) -> str:
    model = get_model()
    slim = {k: v for k, v in metrics.items()
            if k not in ("equity_dates", "equity_values", "trade_log")}
    prompt = f"""You are a quantitative analyst writing a backtest report.
Write exactly 3 paragraphs analyzing these results.

Strategy: {json.dumps(spec, indent=2)}
Metrics: {json.dumps(slim, indent=2)}

Paragraph 1: Summarize strategy performance vs buy-and-hold.
Paragraph 2: Analyze Sharpe ratio, drawdown, and win rate.
Paragraph 3: One concrete recommendation to improve the strategy.
Plain English only. No bullets or headers."""

    response = model.generate_content(prompt)
    return clean_llm_output(response.text)
