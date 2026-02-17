from typing import Annotated
from fastapi import Query
from pydantic import BaseModel


class Subscription(BaseModel):
    model_config = {"populate_by_name": True}
    mode: Annotated[str | None, Query(alias="hub.mode")] = None
    token: Annotated[str | None, Query(alias="hub.verify_token")] = None
    challenge: Annotated[str | None, Query(alias="hub.challenge")] = None
