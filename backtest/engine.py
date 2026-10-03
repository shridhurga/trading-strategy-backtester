import backtrader as bt
import pandas as pd

from backtest.data import fetch_data, add_indicators
from config import DEFAULT_COMMISSION


class EquityRecorder(bt.Analyzer):
    def start(self):
        self.dates = []
        self.equity = []

    def next(self):
        self.dates.append(self.strategy.data.datetime.date(0))
        self.equity.append(self.strategy.broker.getvalue())

    def get_analysis(self):
        return {"dates": self.dates, "equity": self.equity}


class TradeLogger(bt.Analyzer):
    def __init__(self):
        self.trades = []

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades.append({
                "entry_date": bt.num2date(trade.dtopen).isoformat(),
                "exit_date": bt.num2date(trade.dtclose).isoformat(),
                "pnl": round(trade.pnl, 2),
            })


def _buy_hold_return(df: pd.DataFrame, initial_cash: float) -> float:
    if df.empty:
        return 0.0
    shares = initial_cash / df["Close"].iloc[0]
    final = shares * df["Close"].iloc[-1]
    return round((final - initial_cash) / initial_cash * 100, 2)


def _slim_metrics(metrics: dict) -> dict:
    return {k: v for k, v in metrics.items()
            if k not in ("equity_dates", "equity_values", "trade_log")}


def run_backtest(strategy_code: str, ticker: str,
                 start: str, end: str,
                 initial_cash: float = 100000) -> dict:

    df = fetch_data(ticker, start, end)
    df = add_indicators(df)

    namespace = {"backtrader": bt, "bt": bt}
    exec(strategy_code, namespace)
    StrategyClass = namespace["GeneratedStrategy"]

    cerebro = bt.Cerebro()
    cerebro.addstrategy(StrategyClass)
    cerebro.adddata(bt.feeds.PandasData(dataname=df))
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=DEFAULT_COMMISSION)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(EquityRecorder, _name="equity")
    cerebro.addanalyzer(TradeLogger, _name="trade_log")

    results = cerebro.run()
    strat = results[0]
    final = cerebro.broker.getvalue()

    sharpe = strat.analyzers.sharpe.get_analysis()
    dd = strat.analyzers.drawdown.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    equity_data = strat.analyzers.equity.get_analysis()
    trade_log = strat.analyzers.trade_log.trades

    total_trades = trades.get("total", {}).get("total", 0)
    won_trades = trades.get("won", {}).get("total", 0)
    buy_hold = _buy_hold_return(df, initial_cash)
    total_return = round((final - initial_cash) / initial_cash * 100, 2)

    years = max((pd.Timestamp(end) - pd.Timestamp(start)).days / 365.25, 0.1)
    cagr = round(((final / initial_cash) ** (1 / years) - 1) * 100, 2)

    return {
        "ticker": ticker,
        "start": start,
        "end": end,
        "initial_cash": initial_cash,
        "final_value": round(final, 2),
        "total_return": total_return,
        "cagr": cagr,
        "buy_hold_return": buy_hold,
        "alpha_vs_buy_hold": round(total_return - buy_hold, 2),
        "sharpe_ratio": round(sharpe.get("sharperatio", 0) or 0, 3),
        "max_drawdown": round(dd.get("max", {}).get("drawdown", 0), 2),
        "total_trades": total_trades,
        "win_rate": round(won_trades / total_trades * 100, 1) if total_trades else 0,
        "equity_dates": [d.isoformat() for d in equity_data["dates"]],
        "equity_values": [round(v, 2) for v in equity_data["equity"]],
        "trade_log": trade_log,
    }
