import yfinance as yf
import pandas as pd
import logging
from config import TICKERS, PROC_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("fetch")

def get_col(df, keywords):
    """Dynamically find a column by partial name match."""
    for col in df.columns:
        col_str = str(col).lower()
        if any(k.lower() in col_str for k in keywords):
            return df[col]
    return None

def main():
    all_rows = []
    
    for ticker, sector in TICKERS.items():
        log.info(f"Fetching {ticker} ({sector})...")
        try:
            t = yf.Ticker(ticker)
            df = t.quarterly_income_stmt
            
            # Fallback to annual if quarterly fails
            if df is None or df.empty:
                df = t.income_stmt
                
            if df is None or df.empty:
                log.warning(f"{ticker}: No data returned from Yahoo")
                continue
                
            # Transpose so dates are rows
            df = df.transpose().reset_index()
            df = df.rename(columns={"index": "date"})
            
            # Extract using keyword matching
            out = pd.DataFrame()
            out["date"] = df["date"]
            out["revenue"] = get_col(df, ["Total Revenue", "Operating Revenue"])
            out["cogs"] = get_col(df, ["Cost Of Revenue", "Cost of Goods Sold"])
            out["gross_profit"] = get_col(df, ["Gross Profit"])
            out["opex"] = get_col(df, ["Operating Expense"])
            out["operating_income"] = get_col(df, ["Operating Income"])
            out["net_income"] = get_col(df, ["Net Income"])
            
            out["ticker"] = ticker
            out["sector"] = sector
            out["date"] = pd.to_datetime(out["date"], utc=True).dt.tz_localize(None)
            
            all_rows.append(out)
            log.info(f"{ticker}: {len(out)} periods fetched")
            
        except Exception as e:
            log.error(f"{ticker} Failed: {e}")
            
    if not all_rows:
        log.error("No data fetched.")
        return
        
    final = pd.concat(all_rows, ignore_index=True)
    
    # Clean
    before = len(final)
    final = final.dropna(subset=["revenue"])
    final = final[final["revenue"] > 0]
    final = final.sort_values(["ticker", "date"]).reset_index(drop=True)
    
    out_path = PROC_DIR / "financials.parquet"
    final.to_parquet(out_path, index=False)
    
    log.info(f"Saved {len(final)} rows to {out_path}")
    log.info(f"Companies: {final['ticker'].nunique()} | Sectors: {final['sector'].nunique()}")
    log.info("Done.")

if __name__ == "__main__":
    main()