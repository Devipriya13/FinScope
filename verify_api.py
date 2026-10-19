import sys
import requests
from config import FMP_API_KEY, BASE_URL, QUARTERS

print(f"Verifying FMP API at {BASE_URL}")
print(f"Key length: {len(FMP_API_KEY)}")

for ticker in ["AAPL", "MSFT", "WMT"]:
    try:
        r = requests.get(
            f"{BASE_URL}/income-statement",
            params={"symbol": ticker, "period": "quarter",
                    "limit": QUARTERS, "apikey": FMP_API_KEY},
            timeout=20,
        )
        print(f"\n{ticker}: HTTP {r.status_code}")
        print(f"Body preview: {r.text[:300]}")
    except Exception as e:
        print(f"\n{ticker}: EXCEPTION — {e}")

print("\nDone.")