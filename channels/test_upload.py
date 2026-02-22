import httpx
import os
import json

from dotenv import load_dotenv
load_dotenv(override=True)

GRAPH_API_VERSION = os.getenv('GRAPH_API_VERSION', 'v22.0')
if not GRAPH_API_VERSION.startswith('v'):
    GRAPH_API_VERSION = f'v{GRAPH_API_VERSION}'
ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')

# 1. Get app id
debug_url = f'https://graph.facebook.com/debug_token?input_token={ACCESS_TOKEN}&access_token={ACCESS_TOKEN}'
resp = httpx.get(debug_url)
app_id = resp.json().get('data', {}).get('app_id')
print('App ID:', app_id)

if not app_id:
    print("Could not get App ID")
    exit(1)

# Create a dummy image
with open('test_image.jpg', 'wb') as f:
    f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\xd2\x8f\xff\xd9')

file_size = os.path.getsize('test_image.jpg')

# 2. Create upload session
session_url = f'https://graph.facebook.com/{GRAPH_API_VERSION}/{app_id}/uploads'
params = {
    'file_length': file_size,
    'file_type': 'image/jpeg',
    'access_token': ACCESS_TOKEN
}
print(f'Creating upload session for file size {file_size}...')
resp = httpx.post(session_url, params=params)
print(resp.status_code, resp.text)
if resp.status_code != 200:
    exit(1)
session_id = resp.json()['id']
print('Session ID:', session_id)

# 3. Upload file
upload_url = f'https://graph.facebook.com/{session_id}'
headers = {
    'Authorization': f'OAuth {ACCESS_TOKEN}',
    'file_offset': '0'
}
with open('test_image.jpg', 'rb') as f:
    file_data = f.read()
print(f'Uploading file to {upload_url}...')
resp = httpx.post(upload_url, headers=headers, content=file_data)
print(resp.status_code, resp.text)
if resp.status_code != 200:
    exit(1)
h = resp.json()['h']
print('File Handle:', h)

# 4. Update profile picture
print('Updating profile picture with handle...')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
update_url = f'https://graph.facebook.com/{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/whatsapp_business_profile'
headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}
payload = {
    'messaging_product': 'whatsapp',
    'profile_picture_handle': h
}
resp = httpx.post(update_url, headers=headers, json=payload)
print(resp.status_code, resp.text)
