from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class OrderItem(BaseModel):
    item_id: str
    quantity: int
    name: str
    price: float

class SessionState(BaseModel):
    user_id: str
    phone_number: str
    business_phone_number: str
    name: str = "Unknown"
    items: List[OrderItem] = Field(default_factory=list)

    @property
    def cart_total(self) -> float:
        return sum(item.price * item.quantity for item in self.items)

    def add_item(self, item: OrderItem):
        # If item exists, just add quantity
        for existing in self.items:
            if existing.item_id == item.item_id:
                existing.quantity += item.quantity
                return
        self.items.append(item)
        
    def clear_cart(self):
        self.items = []
