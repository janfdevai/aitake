import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
PORT = 8002 # Using the port from the user's running process

async def test_webhook():
    url = f"http://localhost:{PORT}/webhook"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": VERIFY_TOKEN,
        "hub.challenge": "1234567890"
    }
    
    print(f"Sending GET request to {url} with params: {params}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")

    if response.status_code == 200 and response.text == "1234567890":
        print("SUCCESS: Webhook verified successfully.")
    else:
        print("FAILURE: Webhook verification failed.")

if __name__ == "__main__":
    asyncio.run(test_webhook())
