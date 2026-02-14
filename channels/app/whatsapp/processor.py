from fastapi import BackgroundTasks, Request, Response
from typing import Optional
import httpx
import os
import json

from .client import (
    mark_message_as_read,
    send_whatsapp_image_message,
    send_whatsapp_text_message,
    upload_media,
)
from .config import VERIFY_TOKEN
from .models import Subscription
from .utils import process_message_type, remove_extra_one

# Configuration
ORDERBOT_API_URL = os.getenv("ORDERBOT_API_URL", "http://localhost:8001")
DB_API_URL = os.getenv("DB_API_URL", "http://localhost:8000")

def verify_subscription(subscription: Subscription):
    if subscription.mode == "subscribe" and subscription.token == VERIFY_TOKEN:
        return Response(content=subscription.challenge)


async def process_message_answer(response_text: str, image_path: str, from_number: str):
    # 2. Send the message
    if image_path:
        # Note: 'upload_media' might essentially duplicate 'image_path' handling if it expects a local file.
        # Orderbot API returns a path. If both services are local, this works.
        # Ideally, Orderbot API should return a URL or signed URL.
        # Assuming shared volume or local execution for now. 
        image_uploaded = await upload_media(image_path)
        print("IMAGE UPLOADED: ", image_uploaded)
        media_id = image_uploaded.get("id")
        await send_whatsapp_image_message(from_number, response_text, media_id)
    else:
        await send_whatsapp_text_message(from_number, response_text)


async def save_message(conversation_id: str, content: str, sender_type: str):
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "content": content,
                "sender_type": sender_type
            }
            resp = await client.post(f"{DB_API_URL}/conversations/{conversation_id}/messages", json=payload)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error saving message to DB: {e}")


async def run_agent_and_send_reply(message_content: str, from_number: str, business_number: str, client_wa_id: str, client_name: str, conversation_id: Optional[str] = None):
    try:
        # Prepare payload for OrderBot API
        payload = {
            "message": message_content,
            "thread_id": from_number,
            "user": {
                "phone_number": client_wa_id,
                "business_phone_number": business_number,
                "name": client_name,
                "items": [] 
            }
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{ORDERBOT_API_URL}/chat", json=payload, timeout=60.0)
            resp.raise_for_status()
            data = resp.json()
            
            response_text = data.get("message", "")
            print("Response Text: ", response_text)
            image_path = data.get("image_path")
            
            # Save bot response to conversation tracking
            if conversation_id and response_text:
                await save_message(conversation_id, response_text, "bot")
            
            await process_message_answer(response_text, image_path, from_number)

    except Exception as e:
        print(f"Error in background task: {e}")
        error_msg = "Agent is not available right now. Please try again later."
        if conversation_id:
            await save_message(conversation_id, error_msg, "bot")
        await send_whatsapp_text_message(
            from_number, error_msg
        )


async def process_request(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    try:
        entry_list = data.get("entry", [])
        if not entry_list:
            return {"status": "no entry"}
            
        entry = entry_list[0]["changes"][0]["value"]

        if "messages" in entry:
            print("ENTRY", entry)
            business_phone = entry["metadata"]["display_phone_number"]

            # Extract contact info
            contacts = entry.get("contacts", [])
            contact = contacts[0] if contacts else {}
            client_wa_id = contact.get("wa_id")
            client_name = contact.get("profile", {}).get("name", "Unknown")

            print(
                f"Business: {business_phone}, Client WA ID: {client_wa_id}, Name: {client_name}"
            )

            # 1. Resolve Business, Client, and Conversation for tracking
            business_uuid = None
            client_uuid = None
            conversation_id = None
            
            async with httpx.AsyncClient() as client:
                try:
                    # Resolve Business
                    b_resp = await client.get(f"{DB_API_URL}/businesses/by-phone/{business_phone}")
                    if b_resp.status_code == 200:
                        business_uuid = b_resp.json().get("business_id")
                    
                    if business_uuid:
                        # Resolve/Create Client
                        c_check = await client.get(f"{DB_API_URL}/businesses/{business_uuid}/clients/wa/{client_wa_id}")
                        if c_check.status_code == 200:
                            client_uuid = c_check.json().get("client_id")
                        else:
                            new_client = {
                                "wa_id": client_wa_id,
                                "full_name": client_name,
                                "phone_number": client_wa_id
                            }
                            c_resp = await client.post(f"{DB_API_URL}/businesses/{business_uuid}/clients", json=new_client)
                            if c_resp.status_code == 200:
                                client_uuid = c_resp.json().get("client_id")
                        
                        if client_uuid:
                            # Resolve/Create Conversation
                            conv_resp = await client.get(f"{DB_API_URL}/businesses/{business_uuid}/conversations/client/{client_uuid}")
                            if conv_resp.status_code == 200:
                                conversation_id = conv_resp.json().get("conversation_id")
                except Exception as e:
                    print(f"Error in tracking setup: {e}")

            message = entry["messages"][0]
            message_id = message.get("id")
            from_number = remove_extra_one(message["from"])
            
            # Mark as read
            await mark_message_as_read(message_id)
            
            # Process message content
            message_content = await process_message_type(message)
            
            # 2. Save incoming message to conversation tracking
            if conversation_id:
                await save_message(conversation_id, message_content, "client")

            # 3. Process with Agent
            background_tasks.add_task(
                run_agent_and_send_reply,
                message_content,
                from_number,
                business_phone,
                client_wa_id,
                client_name,
                conversation_id
            )
        return {"status": "accepted"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}
