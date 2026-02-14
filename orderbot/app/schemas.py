from typing import Optional, Dict, Any
from pydantic import BaseModel

class UserContext(BaseModel):
    phone_number: str
    business_phone_number: str
    name: Optional[str] = None
    items: Optional[list] = None

class MessageRequest(BaseModel):
    message: str
    thread_id: str
    user: UserContext

class ChatResponse(BaseModel):
    message: str
    image_path: Optional[str] = None
