import requests
import pandas as pd

def test_nav():
    scheme_codes = [119718, 119598, 119723, 119827]
    for code in scheme_codes:
        url = f"https://api.mfapi.in/mf/{code}"
        print(f"Testing {url}...")
        res = requests.get(url)
        data = res.json()
        if data["status"] == "SUCCESS":
            print(f"  ✓ Success: {data['meta']['scheme_name']}")
            print(f"  Latest NAV: {data['data'][0]['nav']} on {data['data'][0]['date']}")
        else:
            print(f"  ✗ Failed for {code}")

if __name__ == "__main__":
    test_nav()
