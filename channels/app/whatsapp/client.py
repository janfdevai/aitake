import os
from .config import client, MESSAGES_URL, MEDIA_URL, HEADERS, WHATSAPP_ACCESS_TOKEN, MIME_TYPE

async def mark_message_as_read(message_id: str):
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {"type": "text"},
    }
    response = await client.post(MESSAGES_URL, json=payload, headers=HEADERS)
    try:
        response.raise_for_status()
    except Exception as e:
        print(f"Error marking message as read: {e}")
        print(f"Response: {response.text}")
        with open("debug_log.txt", "a") as f:
            f.write(f"Error marking message as read: {e}\nResponse: {response.text}\n")

async def send_whatsapp_text_message(to_number: str, text: str):
    print("Sending text message to: ", to_number)
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }
    response = await client.post(MESSAGES_URL, json=payload, headers=HEADERS)
    try:
        response.raise_for_status()
        print(f"Message sent successfully to {to_number}")
        with open("debug_log.txt", "a") as f:
            f.write(f"Message sent successfully to {to_number}: {response.text}\n")
    except Exception as e:
        print(f"Error sending text message: {e}")
        print(f"Response: {response.text}")
        with open("debug_log.txt", "a") as f:
            f.write(f"Error sending text message to {to_number}: {e}\nResponse: {response.text}\n")

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
    response = await client.post(MESSAGES_URL, json=payload, headers=HEADERS)
    try:
        response.raise_for_status()
        print(f"Image message sent successfully to {to_number}")
        with open("debug_log.txt", "a") as f:
            f.write(f"Image message sent successfully to {to_number}: {response.text}\n")
    except Exception as e:
        print(f"Error sending image message: {e}")
        print(f"Response: {response.text}")
        with open("debug_log.txt", "a") as f:
            f.write(f"Error sending image message to {to_number}: {e}\nResponse: {response.text}\n")
