from dotenv import load_dotenv
load_dotenv(override=True)

from app.whatsapp.utils import remove_extra_one

from fastapi import BackgroundTasks, FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.whatsapp import Subscription, process_request, verify_subscription, send_whatsapp_text_message
from app.whatsapp.onboarding import register_phone_number, request_code, verify_code, register_number_with_pin

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello WhatsApp Webhook UPDATED"}


from fastapi import BackgroundTasks, FastAPI, Request, Response, Depends

from fastapi import Query

@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    """Handshake for Meta to verify your server."""
    subscription = Subscription(mode=mode, token=token, challenge=challenge)
    return verify_subscription(subscription) or Response(status_code=403)


@app.post("/webhook")
async def handle_message(request: Request, background_tasks: BackgroundTasks):
    """Receives incoming messages and sends a reply."""
    await process_request(request, background_tasks)
    return {"status": "success"}

class OnboardStartRequest(BaseModel):
    phone_number: str
    display_name: str

@app.post("/whatsapp/onboard/start")
async def start_onboarding(payload: OnboardStartRequest):
    try:
        # 1. Get/Register Phone Number ID
        phone_number_id = await register_phone_number(payload.phone_number, payload.display_name)
        
        # 2. Request OTP
        await request_code(phone_number_id)
        
        return {"status": "success", "phone_number_id": phone_number_id}
    except Exception as e:
        return Response(status_code=400, content=str(e))

class OnboardVerifyRequest(BaseModel):
    phone_number_id: str
    code: str

@app.post("/whatsapp/onboard/verify")
async def verify_onboarding(payload: OnboardVerifyRequest):
    try:
        # 1. Verify OTP
        await verify_code(payload.phone_number_id, payload.code)
        
        # 2. Register the number with a default PIN (user can change later if we expose it, but for now we simplify)
        # This is needed to get out of "Pending" state and enable messaging.
        # PIN format: 6-digit numeric string.
        await register_number_with_pin(payload.phone_number_id, "123456")

        return {"status": "success"}
    except Exception as e:
        return Response(status_code=400, content=str(e))

class MessageRequest(BaseModel):
    phone_number: str
    content: str
    business_phone_number_id: str = None

@app.post("/send-message")
async def send_message(payload: MessageRequest):
    with open("debug_log.txt", "a") as f:
        f.write(f"\n--- Manual Send Request ---\nPhone: {payload.phone_number}, Content: {payload.content}, ID: {payload.business_phone_number_id}\n")
    from_number = remove_extra_one(payload.phone_number)
    await send_whatsapp_text_message(from_number, payload.content, phone_number_id=payload.business_phone_number_id)
    return {"status": "success"}
