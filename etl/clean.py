import json
import pandas as pd
import logging
from config import TICKERS, RAW_DIR, PROCESSED_DIR, SECTOR_MAP, LOG_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("clean")

# The exact metrics we want from the Income Statement
METRICS_MAP = {
    "Total Revenue": "Revenue",
    "Cost Of Revenue": "CostOfRevenue",
    "Gross Profit": "GrossProfit",
    "Operating Income": "OperatingIncome",
    "Net Income": "NetIncome"
}

def clean_ticker(ticker: str) -> pd.DataFrame:
    filepath = RAW_DIR / f"{ticker}.json"
    if not filepath.exists():
        return pd.DataFrame()
        
    with open(filepath, "r") as f:
        data = json.load(f)
        
    income_data = data.get("income")
    if not income_data:
        return pd.DataFrame()
        
    # Convert the dictionary of rows back to a DataFrame
    df = pd.DataFrame.from_dict(income_data, orient="index")
    
    # Filter to only the metrics we need, and rename them
    available_metrics = [m for m in METRICS_MAP.keys() if m in df.index]
    df = df.loc[available_metrics].rename(index=METRICS_MAP)
    
    # Transpose so dates are rows and metrics are columns
    df = df.T.reset_index()
    df = df.rename(columns={"index": "Date"})
    
    # Add company metadata
    df["Ticker"] = ticker
    df["Sector"] = SECTOR_MAP.get(ticker, "Unknown")
    
    return df

def main():
    log.info("Starting data cleaning process...")
    all_data = []
    missing_quarters = 0
    
    for ticker in TICKERS:
        df = clean_ticker(ticker)
        if not df.empty:
            all_data.append(df)
            log.info(f"✅ {ticker}: Cleaned {len(df)} quarters")
            if len(df) < 20:
                missing_quarters += 1
                log.warning(f"⚠️ {ticker} has less than 20 quarters of data")
        else:
            log.error(f"❌ {ticker}: Failed to clean (empty data)")

    if not all_data:
        log.error("No data to save. Check raw files.")
        return

    # Combine all companies into one giant table
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Convert dates to datetime format
    final_df["Date"] = pd.to_datetime(final_df["Date"])
    
    # Convert values to numeric (in case yfinance returned strings)
    numeric_cols = list(METRICS_MAP.values())
    for col in numeric_cols:
        if col in final_df.columns:
            final_df[col] = pd.to_numeric(final_df[col], errors="coerce")

    # Sort by Date and Ticker
    final_df = final_df.sort_values(by=["Date", "Ticker"]).reset_index(drop=True)
    
    # Save to parquet
    out_path = PROCESSED_DIR / "cleaned_financials.parquet"
    final_df.to_parquet(out_path, index=False)
    
    log.info(f"🎉 Cleaned data saved to {out_path}")
    log.info(f"Total rows: {len(final_df)} | Total companies: {len(all_data)}")
    
    # Save a snippet to check
    print("\n--- Preview of Cleaned Data ---")
    print(final_df.tail(5)[["Date", "Ticker", "Revenue", "NetIncome", "Sector"]].to_string(index=False))

if __name__ == "__main__":
    main()
