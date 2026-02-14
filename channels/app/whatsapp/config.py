import os
import httpx

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION")
MIME_TYPE = "image/png"

timeout_config = httpx.Timeout(60.0, connect=10.0)
client = httpx.AsyncClient(timeout=timeout_config)

BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}"
MESSAGES_URL = f"{BASE_URL}/messages"
MEDIA_URL = f"{BASE_URL}/media"

HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}
