"""Offline demo data when Gemini API is unavailable."""

DEMO_SPEC = {
    "ticker": "^NSEI",
    "start": "2019-01-01",
    "end": "2024-01-01",
    "entry_indicator": "SMA",
    "entry_fast": 50,
    "entry_slow": 200,
    "entry_signal": "crossover_above",
    "exit_indicator": "RSI",
    "exit_period": 14,
    "exit_above": 70,
    "exit_below": 30,
    "stop_loss_pct": 0.05,
    "position_size": 0.95,
}

DEMO_CODE = '''
import backtrader as bt

class GeneratedStrategy(bt.Strategy):
    params = (("stop_loss_pct", 0.05), ("position_size", 0.95))

    def __init__(self):
        self.sma_fast = bt.indicators.SMA(self.data.close, period=50)
        self.sma_slow = bt.indicators.SMA(self.data.close, period=200)
        self.rsi = bt.indicators.RSI(self.data.close, period=14)
        self.entry_price = None

    def log(self, txt):
        print(f"{self.datas[0].datetime.date(0)} {txt}")

    def next(self):
        if not self.position:
            crossed = self.sma_fast[0] > self.sma_slow[0] and self.sma_fast[-1] <= self.sma_slow[-1]
            if crossed:
                size = int(self.broker.getcash() * self.p.position_size / self.data.close[0])
                if size > 0:
                    self.log(f"BUY at {self.data.close[0]:.2f}")
                    self.buy(size=size)
                    self.entry_price = self.data.close[0]
        else:
            if self.entry_price is not None:
                stop = self.entry_price * (1 - self.p.stop_loss_pct)
                if self.data.close[0] <= stop:
                    self.log(f"STOP LOSS at {self.data.close[0]:.2f}")
                    self.sell()
                    self.entry_price = None
                    return
            if self.rsi[0] > 70:
                self.log(f"SELL at {self.data.close[0]:.2f}")
                self.sell()
                self.entry_price = None
'''

DEMO_NARRATIVE = (
    "This golden-cross strategy buys when the 50-day SMA crosses above the 200-day SMA "
    "and exits when RSI exceeds 70 or a 5% stop loss is hit. The demo run shows how "
    "trend-following rules behave on historical NIFTY data.\n\n"
    "Sharpe ratio and drawdown together describe whether returns compensated for risk. "
    "A high win rate alone is not enough if losing trades are much larger than winners.\n\n"
    "To improve robustness, test different RSI exit thresholds, add a trailing stop, "
    "or validate the same rules on an out-of-sample period using walk-forward analysis."
)
