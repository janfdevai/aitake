from fastapi import Query
from pydantic import BaseModel

class Subscription(BaseModel):
    mode: str = Query(None, alias="hub.mode")
    token: str = Query(None, alias="hub.verify_token")
    challenge: str = Query(None, alias="hub.challenge")
