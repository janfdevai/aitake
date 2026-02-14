import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from decimal import Decimal
from sqlmodel import Field, Relationship, SQLModel, Column, DateTime, Numeric, text

# 1. ENUMS
class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    preparing = "preparing"
    ready = "ready"
    delivered = "delivered"
    cancelled = "cancelled"

class FulfillmentType(str, Enum):
    delivery = "delivery"
    pickup = "pickup"

class SenderType(str, Enum):
    client = "client"
    business = "business"
    bot = "bot"

# 2. CORE INFRASTRUCTURE
class BusinessManagerLink(SQLModel, table=True):
    __tablename__ = "business_managers"
    business_id: uuid.UUID = Field(foreign_key="businesses.business_id", primary_key=True)
    manager_id: uuid.UUID = Field(foreign_key="managers.manager_id", primary_key=True)

# --- Manager ---
class ManagerBase(SQLModel):
    gcp_uid: str = Field(unique=True, index=True)
    full_name: str
    email: str = Field(unique=True, index=True)

class ManagerRead(ManagerBase):
    manager_id: uuid.UUID
    created_at: datetime

class Manager(ManagerBase, table=True):
    __tablename__ = "managers"
    manager_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("uuid_generate_v4()")}
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    businesses: List["Business"] = Relationship(back_populates="managers", link_model=BusinessManagerLink)

# --- Business ---
class BusinessBase(SQLModel):
    name: str
    whatsapp_phone_number_id: Optional[str] = Field(default=None, unique=True)
    whatsapp_phone_number: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    whatsapp_verify_token: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool = Field(default=True)

class BusinessRead(BusinessBase):
    business_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class Business(BusinessBase, table=True):
    __tablename__ = "businesses"
    business_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("uuid_generate_v4()")}
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    managers: List[Manager] = Relationship(back_populates="businesses", link_model=BusinessManagerLink)
    menu_items: List["MenuItem"] = Relationship(back_populates="business")
    clients: List["Client"] = Relationship(back_populates="business")
    orders: List["Order"] = Relationship(back_populates="business")
    conversations: List["Conversation"] = Relationship(back_populates="business")

# 3. PRODUCT CATALOG
# --- MenuItem ---
class MenuItemBase(SQLModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: Decimal = Field(
        default=0.00,
        sa_column=Column(Numeric(10, 2), nullable=False, server_default=text("0.00"))
    )
    is_available: bool = Field(default=True)

class MenuItemRead(MenuItemBase):
    item_id: uuid.UUID
    business_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class MenuItem(MenuItemBase, table=True):
    __tablename__ = "menu_items"
    item_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("uuid_generate_v4()")}
    )
    business_id: uuid.UUID = Field(foreign_key="businesses.business_id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    business: Business = Relationship(back_populates="menu_items")

# 4. CRM & BOT STATE
# --- Client ---
class ClientBase(SQLModel):
    wa_id: str = Field(index=True)
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class ClientRead(ClientBase):
    client_id: uuid.UUID
    business_id: uuid.UUID
    created_at: datetime

class Client(ClientBase, table=True):
    __tablename__ = "clients"
    client_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("uuid_generate_v4()")}
    )
    business_id: uuid.UUID = Field(foreign_key="businesses.business_id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    business: Business = Relationship(back_populates="clients")
    orders: List["Order"] = Relationship(back_populates="client")
    conversations: List["Conversation"] = Relationship(back_populates="client")

# 5. ORDERS & FULFILLMENT
# --- OrderItem ---
class OrderItemBase(SQLModel):
    item_id: Optional[uuid.UUID] = Field(default=None, foreign_key="menu_items.item_id")
    quantity: int = Field(gt=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemRead(OrderItemBase):
    order_item_id: uuid.UUID
    unit_price: Decimal
    name_snapshot: Optional[str]

class OrderItem(OrderItemBase, table=True):
    __tablename__ = "order_items"
    order_item_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("uuid_generate_v4()")}
    )
    order_id: uuid.UUID = Field(foreign_key="orders.order_id")
    unit_price: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False)
    )
    name_snapshot: Optional[str] = None

    order: "Order" = Relationship(back_populates="items")

# --- Order ---
class OrderBase(SQLModel):
    client_id: Optional[uuid.UUID] = None
    delivery_type: FulfillmentType
    delivery_address: Optional[str] = None

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderRead(OrderBase):
    order_id: uuid.UUID
    business_id: uuid.UUID
    total_amount: Decimal
    status: OrderStatus
    ordered_at: datetime
    updated_at: datetime
    items: List[OrderItemRead]

class Order(OrderBase, table=True):
    __tablename__ = "orders"
    order_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("uuid_generate_v4()")}
    )
    client_id: Optional[uuid.UUID] = Field(default=None, foreign_key="clients.client_id")
    business_id: uuid.UUID = Field(foreign_key="businesses.business_id")
    total_amount: Decimal = Field(
        default=0.00,
        sa_column=Column(Numeric(10, 2), nullable=False, server_default=text("0.00"))
    )
    status: OrderStatus = Field(default=OrderStatus.pending)
    # Fields from Base need to be here if we want constraints or defaults not in Base? 
    # Actually Base has defaults, so we are good.
    
    ordered_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    business: Business = Relationship(back_populates="orders")
    client: Optional[Client] = Relationship(back_populates="orders")
    items: List[OrderItem] = Relationship(back_populates="order")

# 6. CONVERSATIONS
# --- Message ---
class MessageBase(SQLModel):
    sender_type: SenderType
    content: str

class MessageRead(MessageBase):
    message_id: uuid.UUID
    conversation_id: uuid.UUID
    created_at: datetime

class Message(MessageBase, table=True):
    __tablename__ = "messages"
    message_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("uuid_generate_v4()")}
    )
    conversation_id: uuid.UUID = Field(foreign_key="conversations.conversation_id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    conversation: "Conversation" = Relationship(back_populates="messages")

# --- Conversation ---
class ConversationBase(SQLModel):
    last_message: Optional[str] = None

class ConversationRead(ConversationBase):
    conversation_id: uuid.UUID
    business_id: uuid.UUID
    client_id: uuid.UUID
    updated_at: datetime
    # Extra fields for list view
    client_name: Optional[str] = None
    client_wa_id: Optional[str] = None

class Conversation(ConversationBase, table=True):
    __tablename__ = "conversations"
    conversation_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("uuid_generate_v4()")}
    )
    business_id: uuid.UUID = Field(foreign_key="businesses.business_id")
    client_id: uuid.UUID = Field(foreign_key="clients.client_id")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    business: Business = Relationship(back_populates="conversations")
    client: Client = Relationship(back_populates="conversations")
    messages: List[Message] = Relationship(back_populates="conversation")
