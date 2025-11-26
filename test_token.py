import requests

BASE_URL = "http://13.48.124.122/hamasa-api/v1"

IDENTIFIER = "0746424480"   # phone number OR email
PASSWORD = "12345678"


# ----------------------------------------------------------
# 1️⃣ LOGIN (correct version: uses identifier)
# ----------------------------------------------------------
def login(identifier, password):
    url = f"{BASE_URL}/auth/login"
    
    payload = {
        "identifier": identifier,   # THE KEY THE API EXPECTS
        "password": password
    }

    print("[LOGIN] Logging in...")
    r = requests.post(url, json=payload)

    print("STATUS:", r.status_code)
    print("RESPONSE:", r.json())

    if r.status_code != 200:
        raise Exception("Login failed")

    return r.json()["access_token"]


# ----------------------------------------------------------
# 2️⃣ FETCH ACTIVE PROJECTS
# ----------------------------------------------------------
def get_active_projects(token):
    url = f"{BASE_URL}/projects/projects_ml/?page=1&page_size=10&sort=desc"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json"
    }

    print("\n[FETCH] Getting active ML projects...")

    r = requests.get(url, headers=headers)

    print("STATUS:", r.status_code)
    print("RESPONSE:", r.json())

    if r.status_code != 200:
        raise Exception("Failed to fetch active projects")

    return r.json()


# ----------------------------------------------------------
# MAIN TEST FLOW
# ----------------------------------------------------------
if __name__ == "__main__":

    # Step 1: Login & get token
    token = login(IDENTIFIER, PASSWORD)

    # Step 2: Fetch ML projects
    projects = get_active_projects(token)

    print("\nDONE.")
