import os
import aiohttp
from fastapi import HTTPException
from .config import WHATSAPP_ACCESS_TOKEN, GRAPH_API_VERSION

async def get_app_id(access_token: str) -> str:
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/app"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params={"access_token": access_token}) as resp:
            data = await resp.json()
            if "id" not in data:
                raise Exception(f"Failed to get App ID: {data}")
            return data["id"]

async def get_profile(phone_number_id: str) -> dict:
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/whatsapp_business_profile"
    params = {
        "fields": "about,address,description,email,profile_picture_url,websites,vertical",
        "access_token": WHATSAPP_ACCESS_TOKEN
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if "error" in data:
                raise HTTPException(status_code=400, detail=data["error"])
            return data.get("data", [{}])[0]

async def update_profile_picture(phone_number_id: str, file_bytes: bytes, file_type: str) -> dict:
    app_id = await get_app_id(WHATSAPP_ACCESS_TOKEN)
    file_length = len(file_bytes)
    
    # 1. Create upload session
    upload_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{app_id}/uploads"
    params = {
        "file_length": file_length,
        "file_type": file_type,
        "access_token": WHATSAPP_ACCESS_TOKEN
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(upload_url, params=params) as resp:
            data = await resp.json()
            if "error" in data:
                raise HTTPException(status_code=400, detail=f"Upload session failed: {data['error']}")
            upload_session_id = data["id"]
            
    # 2. Upload file to session
    session_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{upload_session_id}"
    headers = {
        "Authorization": f"OAuth {WHATSAPP_ACCESS_TOKEN}",
        "file_offset": "0"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(session_url, headers=headers, data=file_bytes) as resp:
            data = await resp.json()
            if "error" in data:
                raise HTTPException(status_code=400, detail=f"File upload failed: {data['error']}")
            file_handle = data["h"]
            
    # 3. Update profile
    profile_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/whatsapp_business_profile"
    payload = {
        "messaging_product": "whatsapp",
        "profile_picture_handle": file_handle
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(profile_url, params={"access_token": WHATSAPP_ACCESS_TOKEN}, json=payload) as resp:
            data = await resp.json()
            if "error" in data:
                raise HTTPException(status_code=400, detail=f"Profile update failed: {data['error']}")
            return {"status": "success"}
