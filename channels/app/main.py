from dotenv import load_dotenv
from app.whatsapp.utils import remove_extra_one

load_dotenv(override=True)

from fastapi import BackgroundTasks, FastAPI, Request, Response

from app.whatsapp import Subscription, process_request, verify_subscription, send_whatsapp_text_message

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello WhatsApp Webhook"}


@app.get("/webhook")
async def verify_webhook(subscription: Subscription):
    """Handshake for Meta to verify your server."""
    return verify_subscription(subscription) or Response(status_code=403)


@app.post("/webhook")
async def handle_message(request: Request, background_tasks: BackgroundTasks):
    """Receives incoming messages and sends a reply."""
    await process_request(request, background_tasks)
    return {"status": "success"}

@app.post("/send-message")
async def send_message(phone_number: str, content: str):
    from_number = remove_extra_one(phone_number)
    await send_whatsapp_text_message(from_number, content)
    return {"status": "success"}
