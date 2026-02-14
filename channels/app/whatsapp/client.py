import os
from .config import client, MESSAGES_URL, MEDIA_URL, HEADERS, WHATSAPP_ACCESS_TOKEN, MIME_TYPE

async def mark_message_as_read(message_id: str):
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {"type": "text"},
    }
    await client.post(MESSAGES_URL, json=payload, headers=HEADERS)

async def send_whatsapp_text_message(to_number: str, text: str):
    print("Sending text message to: ", to_number)
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }
    await client.post(MESSAGES_URL, json=payload, headers=HEADERS)

async def upload_media(file_path: str):
    upload_headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    }
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, MIME_TYPE)}
        data = {
            "messaging_product": "whatsapp",
            "type": MIME_TYPE,
        }
        response = await client.post(
            MEDIA_URL,
            headers=upload_headers,
            data=data,
            files=files,
        )
    response.raise_for_status()
    return response.json()

async def send_whatsapp_image_message(to_number: str, caption: str, media_id: str):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "image",
        "image": {
            "id": media_id,
            "caption": caption,
        },
    }
    await client.post(MESSAGES_URL, json=payload, headers=HEADERS)
