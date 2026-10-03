import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from config import DEFAULT_CASH, OUTPUT_DIR, TICKER_PRESETS
from core.pipeline import format_api_error, run_full_pipeline

load_dotenv()

PRESETS = json.loads((Path(__file__).parent.parent / "presets" / "strategies.json").read_text())

st.set_page_config(
    page_title="AI Trading Strategy Backtester",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

st.title("AI Trading Strategy Backtester")
st.caption("Final Year Project — Natural language to backtested strategy with validation and comparison.")

tab_run, tab_compare, tab_walk, tab_about = st.tabs([
    "Single Backtest", "Compare Strategies", "Walk-Forward", "About Project"
])

with st.sidebar:
    st.subheader("Settings")
    demo_mode = st.toggle("Demo Mode (no API)", help="Uses built-in golden-cross strategy offline")
    preset = st.selectbox("Market preset", ["Custom"] + list(TICKER_PRESETS.keys()))
    if preset != "Custom":
        st.session_state["ticker"] = TICKER_PRESETS[preset]
    ticker = st.text_input("Ticker", value=st.session_state.get("ticker", "^NSEI"), key="ticker")
    start = st.date_input("Start", value=date(2019, 1, 1))
    end = st.date_input("End", value=date(2024, 1, 1))
    cash = st.number_input("Capital (INR)", value=int(DEFAULT_CASH), step=10000)
    train_ratio = st.slider("Walk-forward train %", 50, 80, 70, help="In-sample portion for validation tab")

    st.markdown("---")
    tpl = st.selectbox("Load template", ["— none —"] + [p["name"] for p in PRESETS])
    if tpl != "— none —":
        chosen = next(p for p in PRESETS if p["name"] == tpl)
        st.session_state["strategy_text"] = chosen["description"]
        if chosen.get("ticker"):
            st.session_state["ticker"] = chosen["ticker"]


def _show_metrics(metrics):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Return", f"{metrics['total_return']}%")
    c2.metric("Buy & Hold", f"{metrics['buy_hold_return']}%")
    c3.metric("Alpha", f"{metrics['alpha_vs_buy_hold']}%")
    c4.metric("Sharpe", metrics["sharpe_ratio"])
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Max Drawdown", f"-{metrics['max_drawdown']}%")
    c6.metric("Win Rate", f"{metrics['win_rate']}%")
    c7.metric("Trades", metrics["total_trades"])
    c8.metric("Final Value", f"INR {metrics['final_value']:,.0f}")


def _show_charts(metrics, ticker, start, end, equity_fig, price_fig, narrative):
    _show_metrics(metrics)
    st.plotly_chart(equity_fig, use_container_width=True)
    st.plotly_chart(price_fig, use_container_width=True)
    if metrics["trade_log"]:
        st.dataframe(pd.DataFrame(metrics["trade_log"]), use_container_width=True)
    st.subheader("AI Analyst Report")
    st.write(narrative)
    equity_fig.write_html(str(OUTPUT_DIR / "chart_output.html"))
    with open(OUTPUT_DIR / "chart_output.html", "rb") as f:
        st.download_button("Download Chart", f.read(), "backtest_chart.html")


with tab_run:
    text = st.text_area(
        "Strategy",
        value=st.session_state.get("strategy_text", ""),
        placeholder="Buy when 50-day SMA crosses above 200-day SMA. Sell when RSI goes above 70.",
        height=100,
        label_visibility="collapsed",
    )
    if st.button("Run Backtest", type="primary"):
        if not demo_mode and not text.strip():
            st.error("Enter a strategy or enable Demo Mode.")
        elif start >= end:
            st.error("Start date must be before end date.")
        else:
            try:
                spec, code, metrics, narrative, ef, pf, is_demo = run_full_pipeline(
                    text, ticker, str(start), str(end), cash, demo_mode
                )
                if is_demo:
                    st.info("Running in Demo Mode — no Gemini API calls used.")
                st.success("Backtest complete.")
                with st.expander("Parsed spec"):
                    st.json(spec)
                with st.expander("Generated code"):
                    st.code(code, language="python")
                _show_charts(metrics, ticker, str(start), str(end), ef, pf, narrative)
            except Exception as e:
                msg = format_api_error(str(e))
                st.error(msg or f"Failed: {e}")

with tab_compare:
    st.write("Compare up to 3 strategies on the same ticker and date range.")
    s1 = st.text_input("Strategy 1", "Buy when 50 SMA crosses 200 SMA. Sell when RSI > 70.")
    s2 = st.text_input("Strategy 2", "Buy when 20 SMA crosses 50 SMA. Sell when RSI > 65.")
    s3 = st.text_input("Strategy 3 (optional)", "")

    if st.button("Compare", type="primary"):
        from backtest.compare import compare_strategies
        from core.pipeline import resolve_strategy
        from reporting.charts import plot_comparison_equity

        strategies = [("Strategy A", s1), ("Strategy B", s2)]
        if s3.strip():
            strategies.append(("Strategy C", s3))

        try:
            runs = []
            for name, desc in strategies:
                if demo_mode:
                    from demo.fallback import DEMO_CODE, DEMO_SPEC
                    spec = {**DEMO_SPEC, "ticker": ticker, "start": str(start), "end": str(end)}
                    code = DEMO_CODE
                else:
                    spec, code, _ = resolve_strategy(desc, ticker, str(start), str(end), False, cash)
                runs.append({"name": name, "code": code, "ticker": ticker,
                             "start": str(start), "end": str(end), "cash": cash})

            result = compare_strategies(runs)
            rows = [{"Strategy": r["name"], **r["metrics"]} for r in result["results"]]
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            st.success(f"Best performer: {result['best']}")
            st.plotly_chart(plot_comparison_equity(result["results"]), use_container_width=True)
        except Exception as e:
            msg = format_api_error(str(e))
            st.error(msg or f"Compare failed: {e}")

with tab_walk:
    st.write("Split history into in-sample (train) and out-of-sample (test) to detect overfitting.")
    wf_text = st.text_area(
        "Strategy for validation",
        value=st.session_state.get(
            "strategy_text",
            "Buy when 50-day SMA crosses above 200-day SMA. Sell when RSI goes above 70.",
        ),
        height=80,
    )
    if st.button("Run Walk-Forward", type="primary"):
        from backtest.walk_forward import run_walk_forward, split_walk_forward
        from core.pipeline import resolve_strategy

        try:
            spec, code, _ = resolve_strategy(wf_text or "Golden cross SMA", ticker, str(start), str(end), demo_mode, cash)
            wf = run_walk_forward(code, ticker, str(start), str(end), cash, train_ratio / 100)
            in_s, in_e, out_s, out_e = split_walk_forward(str(start), str(end), train_ratio / 100)

            st.markdown(f"**In-sample:** {in_s} → {in_e}  |  **Out-of-sample:** {out_s} → {out_e}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### In-Sample")
                st.json(wf["in_sample"])
            with col2:
                st.markdown("#### Out-of-Sample")
                st.json(wf["out_of_sample"])

            st.metric("Return Decay (OOS − IS)", f"{wf['return_decay']}%")
            st.info(wf["verdict"])
        except Exception as e:
            msg = format_api_error(str(e))
            st.error(msg or f"Walk-forward failed: {e}")

with tab_about:
    st.markdown("""
    ### What makes this project unique

    - **Natural language → executable code** — Gemini parses and generates Backtrader strategies
    - **Verify loop** — generated code is validated before results are shown
    - **Buy & hold benchmark** — alpha vs simply holding the asset
    - **Walk-forward validation** — train/test split to detect overfitting
    - **Strategy comparison** — run multiple ideas side-by-side
    - **Demo mode** — full pipeline without API calls for demos and viva

    ### Run locally
    ```bash
    pip install -r requirements.txt
    streamlit run ui/app.py
    python main.py run "Buy when 50 SMA crosses 200 SMA. Sell when RSI > 70."
    ```
    """)
