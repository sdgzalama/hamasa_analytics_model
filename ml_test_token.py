import requests

# -----------------------------
# CONFIGURATION
# -----------------------------
BASE_URL = "http://13.48.124.122/hamasa-api/v1"
SERVICE_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlZjliOWE1Yi1iNGQ5LTRiMGItODE2MC01NDIxNGI0NGEzYTgiLCJyb2xlIjoibWxfc2VydmljZSIsImV4cCI6MTc5NTY3NzkyMn0.ndddw8xmNx_7Rqj1ap58GfQ0jP90WCIMSberTXf1AsU"   # <-- paste full token here


def test_service_token():
    """Test ML Service token by fetching active ML projects."""
    url = f"{BASE_URL}/projects/projects_ml/?page=1&page_size=10&sort=desc"

    headers = {
        "Authorization": f"Bearer {SERVICE_TOKEN}",
        "accept": "application/json"
    }

    print("[TEST] Checking ML Service Token...")

    response = requests.get(url, headers=headers)

    print("\nSTATUS:", response.status_code)
    print("RESPONSE:", response.json())

    if response.status_code == 200:
        print("\n[OK] ML Service Token is valid and working.")
    else:
        print("\n[ERROR] ML Service Token is not valid.")


if __name__ == "__main__":
    test_service_token()
