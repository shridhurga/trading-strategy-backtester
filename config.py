import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

DEFAULT_TICKER = "^NSEI"
DEFAULT_START = "2019-01-01"
DEFAULT_END = "2024-01-01"
DEFAULT_CASH = 100_000.0
DEFAULT_COMMISSION = 0.001

TICKER_PRESETS = {
    "NIFTY 50": "^NSEI",
    "Bank Nifty": "^NSEBANK",
    "Reliance": "RELIANCE.NS",
    "Bitcoin": "BTC-USD",
    "S&P 500": "^GSPC",
}
