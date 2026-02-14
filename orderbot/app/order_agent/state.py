import operator

from langchain.messages import AnyMessage
from typing_extensions import Annotated, TypedDict

from app.order_agent.utils import merge_user


class UserState(TypedDict):
    name: str
    phone_number: str
    business_phone_number: str
    items: list[dict]


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user: Annotated[UserState, merge_user]
    image_path: str
    llm_calls: int
