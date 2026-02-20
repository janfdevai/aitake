import requests
import json
import time

url = "http://127.0.0.1:8000/chat"

payload = {
    "user": {
        "phone_number": "1234567890",
        "business_phone_number": "0987654321",
        "name": "Jane"
    },
    "message": "Hi, I'd like to place an order.",
    "thread_id": "thread_123"
}

headers = {"Content-Type": "application/json"}

try:
    print("Testing connection to OrderBot API...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("\nSuccess!")
        print(f"Bot Response: {response.json().get('message')}")
    else:
        print(f"\nFailed: {response.status_code}")
        print(response.text)
except requests.exceptions.ConnectionError:
    print("Failed to connect. Make sure the server is running.")
