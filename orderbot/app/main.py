import os
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
from app.schemas import MessageRequest, ChatResponse
from app.order_agent.agent import orderbot_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OrderBot API")

@app.get("/")
async def root():
    return {"message": "OrderBot API is running with Google ADK"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request_data: MessageRequest, request: FastAPIRequest):
    try:
        user = request_data.user
        response_text = orderbot_agent.process_message(
            message=request_data.message,
            user_phone=user.phone_number,
            business_phone=user.business_phone_number,
            name=user.name if user.name else "Unknown"
        )
        
        print(response_text)
        
        # We omitted image_path handling for now
        return ChatResponse(message=response_text, image_path=None)
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
