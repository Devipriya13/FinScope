import pandas as pd
import numpy as np
import logging
import os
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_percentage_error
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("forecast")

def main():
    log.info("Starting forecasting pipeline...")
    
    # 1. Automatically find the CSV file
    possible_paths = [
        'Company_income_statement.csv',           
        '../Company_income_statement.csv',        
        '../data/Company_income_statement.csv',   
        'data/Company_income_statement.csv'
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
            
    if not csv_path:
        log.error("❌ Could not find Company_income_statement.csv!")
        return
        
    log.info(f"Found dataset at: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Ensure Revenue is numeric
    df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
    
    # 2. Filter to only Q1-Q4 (remove FY) and the 20 tickers
    tickers = ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "CRM", "ADBE", "ORCL", "AVGO", 
               "WMT", "COST", "PG", "KO", "PEP", "NKE", "MCD", "SBUX", "TGT", "AMZN"]
    df = df[df['Ticker'].isin(tickers)]
    df = df[df['Fiscal Period'].isin(['Q1', 'Q2', 'Q3', 'Q4'])]
    
    # Create a proper Date column
    def get_q_date(row):
        year = int(row['Fiscal Year'])
        q = row['Fiscal Period']
        month = 3 if q == 'Q1' else 6 if q == 'Q2' else 9 if q == 'Q3' else 12
        return pd.Timestamp(year=year, month=month, day=28)

    df['Date'] = df.apply(get_q_date, axis=1)
    
    tech = ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "CRM", "ADBE", "ORCL", "AVGO"]
    df['Sector'] = np.where(df['Ticker'].isin(tech), 'Tech', 'Consumer')
    
    # 3. Aggregate by Date and Sector
    sector_df = df.groupby(["Date", "Sector"])["Revenue"].sum().reset_index()
    sector_df = sector_df.sort_values(["Sector", "Date"])
    
    results = []
    metrics = []
    
    # 4. Train models for each sector
    for sector in sector_df["Sector"].unique():
        s_df = sector_df[sector_df["Sector"] == sector].copy()
        s_df = s_df.set_index("Date")
        
        # Create lag features for XGBoost
        s_df["Lag_1"] = s_df["Revenue"].shift(1)
        s_df["Lag_4"] = s_df["Revenue"].shift(4)
        s_df["Rolling_Mean_4"] = s_df["Revenue"].rolling(4).mean()
        s_df = s_df.dropna()
        
        # Time-based split: Train on all but last 4 quarters, test on last 4
        train = s_df.iloc[:-4]
        test = s_df.iloc[-4:]
        
        # --- Model 1: Naive Forecast ---
        naive_preds = test["Lag_1"]
        naive_mape = mean_absolute_percentage_error(test["Revenue"], naive_preds) * 100
        
        # --- Model 2: XGBoost ---
        features = ["Lag_1", "Lag_4", "Rolling_Mean_4"]
        X_train, y_train = train[features], train["Revenue"]
        X_test = test[features]
        
        model = XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=3, random_state=42)
        model.fit(X_train, y_train)
        xgb_preds = model.predict(X_test)
        xgb_mape = mean_absolute_percentage_error(test["Revenue"], xgb_preds) * 100
        
        log.info(f"✅ {sector} | Naive MAPE: {naive_mape:.2f}% | XGBoost MAPE: {xgb_mape:.2f}%")
        
        metrics.append({"Sector": sector, "Model": "Naive", "MAPE": naive_mape})
        metrics.append({"Sector": sector, "Model": "XGBoost", "MAPE": xgb_mape})
        
        for date in test.index:
            results.append({
                "Date": date, "Sector": sector, 
                "Actual": test.loc[date, "Revenue"],
                "Naive_Forecast": test.loc[date, "Lag_1"],
                "XGBoost_Forecast": xgb_preds[test.index.get_loc(date)]
            })

    # 5. Save outputs 
    pd.DataFrame(results).to_csv('../forecast_results.csv', index=False)
    pd.DataFrame(metrics).to_csv('../model_metrics.csv', index=False)
    log.info("🎉 Forecasting complete. Results saved.")

if __name__ == "__main__":
    main()