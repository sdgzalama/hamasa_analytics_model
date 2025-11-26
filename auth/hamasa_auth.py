# import requests
# import os

# BASE_URL = os.getenv("HAMASA_API_URL", "http://13.48.124.122/hamasa-api/v1")
# HAMASA_IDENTIFIER = os.getenv("HAMASA_IDENTIFIER", "0746424480")
# HAMASA_PASSWORD = os.getenv("HAMASA_PASSWORD", "12345678")

# def get_token():
#     """Login and return access token."""
#     url = f"{BASE_URL}/auth/login"

#     payload = {
#         "identifier": HAMASA_IDENTIFIER,
#         "password": HAMASA_PASSWORD
#     }

#     r = requests.post(url, json=payload)

#     if r.status_code != 200:
#         print("[AUTH ERROR]", r.status_code, r.text)
#         return None

#     return r.json()["access_token"]
