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

def verify_subscription(subscription: Subscription):
    if subscription.mode == "subscribe" and subscription.token == VERIFY_TOKEN:
        return Response(content=subscription.challenge)


async def process_message_answer(response_text: str, image_path: str, from_number: str, phone_number_id: str):
    # 2. Send the message
    if image_path:
        # Note: 'upload_media' might essentially duplicate 'image_path' handling if it expects a local file.
        # Orderbot API returns a path. If both services are local, this works.
        # Ideally, Orderbot API should return a URL or signed URL.
        # Assuming shared volume or local execution for now. 
        image_uploaded = await upload_media(image_path, phone_number_id=phone_number_id)
        print("IMAGE UPLOADED: ", image_uploaded)
        media_id = image_uploaded.get("id")
        await send_whatsapp_image_message(from_number, response_text, media_id, phone_number_id=phone_number_id)
    else:
        await send_whatsapp_text_message(from_number, response_text, phone_number_id=phone_number_id)


from .supabase_client import supabase

async def save_message(conversation_id: str, content: str, sender_type: str):
    try:
        payload = {
            "conversation_id": conversation_id,
            "content": content,
            "sender_type": sender_type
        }
        supabase.table("messages").insert(payload).execute()
    except Exception as e:
        print(f"Error saving message to Supabase: {e}")


async def run_agent_and_send_reply(message_content: str, from_number: str, business_number: str, client_wa_id: str, client_name: str, conversation_id: Optional[str] = None, phone_number_id: Optional[str] = None):
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
        
        with open("debug_log.txt", "a") as f:
            f.write(f"Calling OrderBot at {ORDERBOT_API_URL}/chat with payload: {json.dumps(payload)}\n")
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{ORDERBOT_API_URL}/chat", json=payload, timeout=60.0)
            with open("debug_log.txt", "a") as f:
                f.write(f"OrderBot status: {resp.status_code}\n")
            resp.raise_for_status()
            data = resp.json()
            
            response_text = data.get("message", "")
            image_path = data.get("image_path")
            print(f"Agent Response: {response_text}, Image Path: {image_path}")
            
            # Save bot response to conversation tracking
            if conversation_id and response_text:
                await save_message(conversation_id, response_text, "bot")
            
            await process_message_answer(response_text, image_path, from_number, phone_number_id)

    except Exception as e:
        with open("debug_log.txt", "a") as f:
            f.write(f"Error in background task: {e}\n")
        print(f"Error in background task: {e}")
        error_msg = "Agent is not available right now. Please try again later."
        if conversation_id:
            await save_message(conversation_id, error_msg, "bot")
        await send_whatsapp_text_message(
            from_number, error_msg, phone_number_id=phone_number_id
        )


async def process_request(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    with open("debug_log.txt", "a") as f:
        f.write(f"\n--- New Request ---\n{json.dumps(data, indent=2)}\n")
    try:
        entry_list = data.get("entry", [])
        if not entry_list:
            print("No entry found in webhook data")
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
            
            try:
                # Resolve Business
                all_b = supabase.table("businesses").select("*").execute()
                with open("debug_log.txt", "a") as f:
                    f.write(f"All businesses in DB: {all_b.data}\n")
                b_query = supabase.table("businesses").select("business_id").eq("whatsapp_phone_number", business_phone).execute()
                with open("debug_log.txt", "a") as f:
                    f.write(f"Business query result: {b_query.data}\n")
                if b_query.data:
                    business_uuid = b_query.data[0].get("business_id")
                    whatsapp_phone_number_id = b_query.data[0].get("whatsapp_phone_number_id")
                
                if business_uuid:
                    # Resolve/Create Client
                    c_query = supabase.table("clients").select("client_id").eq("business_id", business_uuid).eq("wa_id", client_wa_id).execute()
                    if c_query.data:
                        client_uuid = c_query.data[0].get("client_id")
                    else:
                        new_client = {
                            "business_id": business_uuid,
                            "wa_id": client_wa_id,
                            "full_name": client_name,
                            "phone_number": client_wa_id
                        }
                        c_insert = supabase.table("clients").insert(new_client).execute()
                        if c_insert.data:
                            client_uuid = c_insert.data[0].get("client_id")
                            print(f"Created new client: {client_uuid}")
                    
                    if client_uuid:
                        # Resolve/Create Conversation
                        conv_query = supabase.table("conversations").select("conversation_id").eq("business_id", business_uuid).eq("client_id", client_uuid).execute()
                        if conv_query.data:
                            conversation_id = conv_query.data[0].get("conversation_id")
                        else:
                            new_conv = {
                                "business_id": business_uuid,
                                "client_id": client_uuid
                            }
                            conv_insert = supabase.table("conversations").insert(new_conv).execute()
                            if conv_insert.data:
                                conversation_id = conv_insert.data[0].get("conversation_id")
                                print(f"Created new conversation: {conversation_id}")
            except Exception as e:
                with open("debug_log.txt", "a") as f:
                    f.write(f"Supabase Error: {e}\n")
                print(f"Error in Supabase tracking setup: {e}")

            message = entry["messages"][0]
            message_id = message.get("id")
            from_number = message.get("from")
            # Mark as read
            # Determine phone_number_id from entry metadata if possible, but for now using the one from DB or None
            # Actually entry metadata has id
            payload_phone_number_id = entry["metadata"].get("phone_number_id")
            resolved_phone_number_id = whatsapp_phone_number_id if 'whatsapp_phone_number_id' in locals() and whatsapp_phone_number_id else payload_phone_number_id
            
            await mark_message_as_read(message_id, phone_number_id=resolved_phone_number_id)
            
            # Process message content
            message_content = await process_message_type(message)
            with open("debug_log.txt", "a") as f:
                f.write(f"Processed Message: {message_content}, From: {from_number}, Business: {business_phone}\n")
                f.write(f"Resolved business_uuid: {business_uuid}, client_uuid: {client_uuid}, conversation_id: {conversation_id}\n")
            print(f"Message from {from_number}: {message_content}")
            
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
                conversation_id,
                resolved_phone_number_id
            )
        return {"status": "accepted"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}
