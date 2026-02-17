import requests
import sys

url = "http://127.0.0.1:8000/api/auth/token"
payload = {
    "username": "admin",
    "password": "1234"
}

print(f"Attempting login to {url} with {payload}...")

try:
    response = requests.post(url, data=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
