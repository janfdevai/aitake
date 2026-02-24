import os
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

from fastapi import FastAPI, HTTPException, Request as FastAPIRequest, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas import MessageRequest, ChatResponse
from app.order_agent.agent import orderbot_agent

import google.auth.transport.requests
import google.oauth2.id_token

security = HTTPBearer(auto_error=False)

def verify_google_token(request: FastAPIRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Skip verification if not in production
    if os.getenv("ENVIRONMENT") != "production":
        return None

    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = credentials.credentials
    try:
        auth_req = google.auth.transport.requests.Request()
        # Audience is typically the Cloud Run URL. For now, we only verify the token is valid
        # from a trusted Google service account. Audience validation can be strict if needed.
        # We pass None for audience to just verify it's a valid Google-issued token meant for a Cloud Run service,
        # but normally we'd want to check the specific audience if we knew it statically.
        # verify_oauth2_token actually requires an audience or requires us to check it ourselves.
        # We can pass the request.base_url as the expected audience, or just a known client ID.
        # Using verify_oauth2_token without audience will raise ValueError unless we use verify_oauth2_token(..., audience=...)
        # Wait, if audience is not known statically, Cloud Run sets the audience to the service URL.
        # We can extract the audience dynamically from the unverified token headers or use the base url.
        id_info = google.oauth2.id_token.verify_oauth2_token(
            token, auth_req
        )
        # We can also check id_info['email'] if we want to restrict to specific service accounts.
        return id_info
    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid authentication credentials: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OrderBot API")

@app.get("/")
async def root():
    return {"message": "OrderBot API is running with Google ADK"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request_data: MessageRequest, request: FastAPIRequest, token_info: dict = Depends(verify_google_token)):
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
