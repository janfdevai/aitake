from dotenv import load_dotenv
load_dotenv(override=True)

from app.whatsapp.utils import remove_extra_one

from fastapi import BackgroundTasks, FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.whatsapp import Subscription, process_request, verify_subscription, send_whatsapp_text_message

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

class MessageRequest(BaseModel):
    phone_number: str
    content: str

@app.post("/send-message")
async def send_message(payload: MessageRequest):
    with open("debug_log.txt", "a") as f:
        f.write(f"\n--- Manual Send Request ---\nPhone: {payload.phone_number}, Content: {payload.content}\n")
    from_number = remove_extra_one(payload.phone_number)
    await send_whatsapp_text_message(from_number, payload.content)
    return {"status": "success"}
