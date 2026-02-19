import phonenumbers
from .config import (
    client, 
    WHATSAPP_ACCESS_TOKEN, 
    WHATSAPP_BUSINESS_ACCOUNT_ID, 
    GRAPH_API_VERSION,
    HEADERS
)

async def register_phone_number(phone_number: str, display_name: str):
    """
    Registers a phone number with the WhatsApp Business API.
    This is a simplification. In a real tech provider scenario, 
    you'd use the Embedded Signup flow or calls to the WABA to add the number first.
    
    For this implementation, we first check if the number is in the WABA.
    If not, we attempt to add it using the WABA API.
    """
    # 1. Get Phone Number ID
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{WHATSAPP_BUSINESS_ACCOUNT_ID}/phone_numbers"
    
    try:
        response = await client.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching phone numbers: {e}")
        # Proceed to try adding anyway if fetch fails? Or better to fail.
        # Let's assume empty list if fetch fails or just re-raise.
        if response.status_code == 400: # WABA might not exist or permission issue
             raise Exception(f"Failed to access WABA phone numbers: {e}")
        data = {'data': []}

    phone_number_id = None
    clean_input_phone = phone_number.replace('+', '').replace(' ', '')
    
    for item in data.get('data', []):
        # API returns numbers in various formats, need to normalize or check endsWith
        api_phone = item.get('display_phone_number', '').replace(' ', '').replace('+', '').replace('-', '')
        if api_phone.endswith(clean_input_phone) or clean_input_phone.endswith(api_phone):
             phone_number_id = item.get('id')
             break
             
    if not phone_number_id:
        print(f"Phone number {phone_number} not found in WABA {WHATSAPP_BUSINESS_ACCOUNT_ID}. Attempting to add it...")
        try:
            # Parse number to get CC and National Number
            # Ensure proper format with +
            if not phone_number.startswith('+'):
                phone_number_to_parse = f"+{phone_number}"
            else:
                phone_number_to_parse = phone_number
                
            parsed_number = phonenumbers.parse(phone_number_to_parse, None)
            if not phonenumbers.is_valid_number(parsed_number):
                 raise Exception("Invalid phone number format")
                 
            cc = str(parsed_number.country_code)
            national_number = str(parsed_number.national_number)
            
            add_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{WHATSAPP_BUSINESS_ACCOUNT_ID}/phone_numbers"
            payload = {
                "cc": cc,
                "phone_number": national_number,
                "verified_name": display_name
            }
            
            print(f"Adding phone number with payload: {payload}")
            add_response = await client.post(add_url, json=payload, headers=HEADERS)
            if add_response.status_code != 200:
                 print(f"Failed to add number: {add_response.text}")
                 add_response.raise_for_status()
                 
            add_data = add_response.json()
            phone_number_id = add_data.get('id')
            print(f"Successfully added phone number. ID: {phone_number_id}")
            
        except Exception as e:
            raise Exception(f"Failed to add phone number to WABA automatically: {e}. Please add it manually in Facebook Business Manager.")


    return phone_number_id

async def register_number_with_pin(phone_number_id: str, pin: str):
    """
    Registers the phone number for messaging and sets the 2FA PIN.
    This is required before the number can send/receive messages or request OTPs.
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/register"
    payload = {
        "messaging_product": "whatsapp",
        "pin": pin
    }
    print(f"Registering phone number ID {phone_number_id} with PIN...")
    try:
        response = await client.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        print("Registration successful.")
        return response.json()
    except Exception as e:
        print(f"Registration failed: {e}")
        # If it's already registered, we might get an error, but that's okay.
        # We can inspect response.content if needed.
        if response.status_code != 200:
             print(f"Response: {response.text}")
        raise e

async def request_code(phone_number_id: str):
    """
    Triggers the OTP code via SMS.
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/request_code"
    payload = {
        "code_method": "SMS",
        "language": "en_US"
    }
    response = await client.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()

async def verify_code(phone_number_id: str, code: str):
    """
    Verifies the OTP code.
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/verify_code"
    payload = {
        "code": code
    }
    response = await client.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()
