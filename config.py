from pathlib import Path

RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")
for d in (RAW_DIR, PROC_DIR):
    d.mkdir(parents=True, exist_ok=True)

TICKERS = {
    "AAPL": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Technology",
    "META": "Technology",
    "NVDA": "Technology",
    "WMT": "Consumer",
    "COST": "Consumer",
    "KO": "Consumer",
    "PG": "Consumer",
    "AMZN": "Consumer",
}