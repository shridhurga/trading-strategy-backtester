import yfinance as yf
import pandas as pd

def fetch_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = yf.download(ticker, start=start, end=end, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data found for {ticker}")
    df.index = pd.to_datetime(df.index)
    df.columns = df.columns.get_level_values(0)
    return df[["Open", "High", "Low", "Close", "Volume"]]

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["SMA_50"]  = df["Close"].rolling(window=50).mean()
    df["SMA_200"] = df["Close"].rolling(window=200).mean()
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(window=14).mean()
    loss = -delta.clip(upper=0).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    exp1 = df["Close"].ewm(span=12, adjust=False).mean()
    exp2 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = exp1 - exp2
    df["MACD_SIG"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df.dropna()

if __name__ == "__main__":
    print("Fetching NIFTY50 data...")
    df = fetch_data("^NSEI", "2019-01-01", "2024-01-01")
    df = add_indicators(df)
    print(df.tail())
    print("Shape:", df.shape)
    print("Columns:", list(df.columns))
    print("Data fetch successful!")