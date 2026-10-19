import json
import logging
import pandas as pd
from config import TICKERS, RAW_DIR, PROC_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("clean")

def main():
    rows = []
    for ticker, sector in TICKERS.items():
        path = RAW_DIR / f"{ticker}.json"
        if not path.exists():
            log.warning(f"{ticker}: no raw file, skipping")
            continue
            
        with open(path) as f:
            payload = json.load(f)

        records = payload.get("data", [])
        
        for q in records:
            # Tiingo uses slightly different field names
            rnd = q.get("researchAndDevelopment") or 0
            sga = q.get("sellingGeneralAndAdministrative") or 0
            
            # Some companies report opex directly, some don't
            opex_direct = q.get("operatingExpenses")
            opex = opex_direct if opex_direct else (rnd + sga)

            rows.append({
                "ticker": ticker,
                "sector": sector,
                "date": q.get("date"),
                "revenue": q.get("revenue"),
                "cogs": q.get("costOfRevenue"),
                "gross_profit": q.get("grossProfit"),
                "rd_expense": rnd,
                "sga_expense": sga,
                "opex": opex,
                "operating_income": q.get("operatingIncome"),
                "net_income": q.get("netIncome"),
            })

    df = pd.DataFrame(rows)
    before = len(df)

    if before == 0:
        log.error("No data extracted! Check your raw JSON files.")
        return

    # Cleaning rules
    df = df.dropna(subset=["revenue"])
    df = df[df["revenue"] > 0]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    df = df.drop_duplicates(subset=["ticker", "date"], keep="last")
    
    after = len(df)
    log.info(f"Cleaning: {before} -> {after} rows ({before - after} dropped)")

    # Write cleaning log
    with open("cleaning_log.md", "w", encoding="utf-8") as f:
        f.write("# Cleaning Log\n\n")
        f.write("| Rule | Rows Affected |\n|---|---:|\n")
        f.write(f"| Rows before cleaning | {before} |\n")
        f.write(f"| Dropped null / non-positive revenue | {before - after} |\n")
        f.write(f"| Rows after cleaning | {after} |\n")

    PROC_DIR.mkdir(parents=True, exist_ok=True)
    out = PROC_DIR / "financials.parquet"
    df.to_parquet(out, index=False)

    log.info(f"Saved {len(df)} rows to {out}")
    log.info(f"Companies: {df['ticker'].nunique()} | Sectors: {df['sector'].nunique()}")
    log.info(f"Date range: {df['date'].min().date()} -> {df['date'].max().date()}")
    log.info("Done.")

if __name__ == "__main__":
    main()