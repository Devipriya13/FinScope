import yfinance as yf
import logging
import time
import json
from config import TICKERS, RAW_DIR, LOG_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "etl.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("fetch")

def fetch_ticker(ticker: str):
    log.info(f"Fetching {ticker}...")
    try:
        t = yf.Ticker(ticker)
        
        # Fetch the 3 main financial statements
        income = t.quarterly_income_stmt
        balance = t.quarterly_balance_sheet
        cashflow = t.quarterly_cashflow
        
        # We store them in a dictionary and convert to JSON format
        data = {}
        for name, df in [("income", income), ("balance", balance), ("cashflow", cashflow)]:
            if not df.empty:
                # Convert dates to strings so JSON can save it
                df_copy = df.copy()
                df_copy.columns = df_copy.columns.astype(str)
                data[name] = df_copy.to_dict(orient="index")
            else:
                data[name] = None
                log.warning(f"{ticker}: {name} statement is empty")

        # Save to data/raw/AAPL.json
        out_path = RAW_DIR / f"{ticker}.json"
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
            
        log.info(f"✅ {ticker} saved to {out_path}")
        
    except Exception as e:
        log.error(f"❌ {ticker} failed: {e}")

def main():
    log.info(f"Starting fetch for {len(TICKERS)} tickers")
    start = time.time()
    
    for i, ticker in enumerate(TICKERS, 1):
        log.info(f"[{i}/{len(TICKERS)}] Processing {ticker}")
        fetch_ticker(ticker)
        time.sleep(1.5)  # Pause to avoid Yahoo rate-limiting us
        
    elapsed = time.time() - start
    log.info(f"Done in {elapsed:.1f}s.")

if __name__ == '__main__':
    main()
