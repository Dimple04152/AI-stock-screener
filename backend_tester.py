import requests
import time

BASE_URL = "http://localhost:8000"

def test_backend():
    print("--- Phase 1: Authentication ---")
    # 1. Login
    login_data = {"username": "testuser", "password": "password123"}
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Login successful. Token obtained.")
        else:
            print(f"❌ Login failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Connection error: {e}. Is the server running (uvicorn main:app)?")
        return

    headers = {"Authorization": f"Bearer {token}"}

    print("\n--- Phase 2: Natural Language Query ---")
    # 2. Test AI Query
    query_payload = {"query": "Technology companies with PE ratio < 40"}
    print(f"Sending Query: {query_payload['query']}")
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/query/", json=query_payload, headers=headers)
    end_time = time.time()

    if response.status_code == 200:
        results = response.json().get("results", [])
        print(f"✅ AI Query Success ({round(end_time - start_time, 2)}s)")
        print(f"Found {len(results)} companies:")
        for res in results:
            print(f" - {res['symbol']}: {res['company_name']} (Sector: {res['sector']})")
    else:
        print(f"❌ Query failed: {response.status_code} - {response.text}")

    print("\n--- Phase 3: Portfolio View ---")
    # 3. Test Portfolio
    response = requests.get(f"{BASE_URL}/portfolio/", headers=headers)
    if response.status_code == 200:
        portfolio = response.json()
        print(f"✅ Portfolio fetched. Items: {len(portfolio)}")
        for item in portfolio:
            print(f" - {item['symbol']}: Current Price ${item['current_price']:.2f} (P/L: ${item['profit_loss']:.2f})")
    else:
        print(f"❌ Portfolio failed: {response.text}")

if __name__ == "__main__":
    test_backend()
