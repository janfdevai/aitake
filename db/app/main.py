from contextlib import asynccontextmanager
from typing import List, Optional
import os
import uuid
import httpx

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session, create_db_and_tables
from app.models import (
    Business, BusinessRead, MenuItem, MenuItemRead, Client, ClientRead, 
    Order, OrderCreate, OrderRead, OrderItem,
    OrderStatus, FulfillmentType, Manager, ManagerRead,
    BusinessManagerLink, Conversation, ConversationRead, Message, MessageRead, SenderType
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This assumes the tables already exist from the SQL script, 
    # but create_db_and_tables() won't hurt if they already exist 
    # (except maybe for the custom Enum types if not handled carefully).
    # Since the user provided a schema.sql, they probably ran it.
    # create_db_and_tables()
    yield

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FastOrder API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHANNELS_API_URL = os.getenv("CHANNELS_API_URL", "http://localhost:8002")

@app.get("/")
async def root():
    return {"message": "FastOrder API is running"}


# --- MANAGERS ---
@app.get("/managers/login", response_model=ManagerRead)
def manager_login(email: str, session: Session = Depends(get_session)):
    statement = select(Manager).where(Manager.email == email)
    manager = session.exec(statement).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    return manager

@app.get("/managers/{manager_id}/businesses", response_model=List[BusinessRead])
def read_manager_businesses(manager_id: uuid.UUID, session: Session = Depends(get_session)):
    manager = session.get(Manager, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    return manager.businesses

@app.post("/managers", response_model=ManagerRead)
def create_manager(manager: Manager, session: Session = Depends(get_session)):
    session.add(manager)
    session.commit()
    session.refresh(manager)
    return manager


# --- BUSINESSES ---
@app.get("/businesses", response_model=List[BusinessRead])
def read_businesses(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    session: Session = Depends(get_session)
):
    businesses = session.exec(select(Business).offset(offset).limit(limit)).all()
    return businesses

@app.get("/businesses/{business_id}", response_model=BusinessRead)
def read_business(business_id: uuid.UUID, session: Session = Depends(get_session)):
    business = session.get(Business, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business

@app.get("/businesses/by-phone/{phone_number}", response_model=BusinessRead)
def read_business_by_phone(phone_number: str, session: Session = Depends(get_session)):
    # Try to match whatsapp_phone_number (exact match)
    statement = select(Business).where(Business.whatsapp_phone_number == phone_number)
    business = session.exec(statement).first()
    
    if not business:
        # Fallback: check if it matches whatsapp_phone_number_id
        statement = select(Business).where(Business.whatsapp_phone_number_id == phone_number)
        business = session.exec(statement).first()
        
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business

@app.post("/businesses", response_model=BusinessRead)
def create_business(
    business: Business,
    manager_id: Optional[uuid.UUID] = Query(default=None),
    session: Session = Depends(get_session)
):
    session.add(business)
    session.flush()
    if manager_id:
        link = BusinessManagerLink(business_id=business.business_id, manager_id=manager_id)
        session.add(link)
    session.commit()
    session.refresh(business)
    return business

@app.patch("/businesses/{business_id}", response_model=BusinessRead)
def update_business(
    business_id: uuid.UUID,
    business_update: Business, # For simplicity, using Business model, but in production use an Update model
    session: Session = Depends(get_session)
):
    db_business = session.get(Business, business_id)
    if not db_business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    data = business_update.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key != "business_id":
            setattr(db_business, key, value)
    
    session.add(db_business)
    session.commit()
    session.refresh(db_business)
    return db_business


# --- MENU ITEMS ---
@app.get("/businesses/{business_id}/menu", response_model=List[MenuItemRead])
def read_menu_items(
    business_id: uuid.UUID,
    session: Session = Depends(get_session)
):
    statement = select(MenuItem).where(MenuItem.business_id == business_id)
    items = session.exec(statement).all()
    return items

@app.post("/businesses/{business_id}/menu", response_model=MenuItemRead)
def create_menu_item(
    business_id: uuid.UUID,
    item: MenuItem,
    session: Session = Depends(get_session)
):
    item.business_id = business_id
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@app.patch("/menu/{item_id}", response_model=MenuItemRead)
def update_menu_item(
    item_id: uuid.UUID,
    item_update: MenuItem,
    session: Session = Depends(get_session)
):
    db_item = session.get(MenuItem, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    data = item_update.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key != "item_id" and key != "business_id":
            setattr(db_item, key, value)
    
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# --- CLIENTS ---
@app.get("/businesses/{business_id}/clients/wa/{wa_id}", response_model=ClientRead)
def read_client_by_wa(
    business_id: uuid.UUID,
    wa_id: str,
    session: Session = Depends(get_session)
):
    statement = select(Client).where(Client.business_id == business_id, Client.wa_id == wa_id)
    client = session.exec(statement).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@app.post("/businesses/{business_id}/clients", response_model=ClientRead)
def create_client(
    business_id: uuid.UUID,
    client: Client,
    session: Session = Depends(get_session)
):
    client.business_id = business_id
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


# --- ORDERS ---
@app.post("/businesses/{business_id}/orders", response_model=OrderRead)
def create_order(
    business_id: uuid.UUID,
    order_data: OrderCreate,
    session: Session = Depends(get_session)
):
    # Check if client exists
    if order_data.client_id:
        client = session.get(Client, order_data.client_id)
        if not client or client.business_id != business_id:
            raise HTTPException(status_code=400, detail="Invalid client_id for this business")

    # Create order object
    db_order = Order(
        business_id=business_id,
        client_id=order_data.client_id,
        delivery_type=order_data.delivery_type,
        delivery_address=order_data.delivery_address,
        status=OrderStatus.pending
    )
    session.add(db_order)
    session.flush() # Populate order_id

    total = 0
    for item_data in order_data.items:
        # Verify item exists and belongs to business
        menu_item = session.get(MenuItem, item_data.item_id)
        if not menu_item or menu_item.business_id != business_id:
            raise HTTPException(status_code=400, detail=f"Invalid item_id: {item_data.item_id}")
        
        db_item = OrderItem(
            order_id=db_order.order_id,
            item_id=item_data.item_id,
            quantity=item_data.quantity,
            unit_price=menu_item.price,
            name_snapshot=menu_item.name
        )
        total += db_item.unit_price * db_item.quantity
        session.add(db_item)
    
    db_order.total_amount = total
    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    return db_order

@app.get("/businesses/{business_id}/orders", response_model=List[OrderRead])
def read_orders(
    business_id: uuid.UUID,
    status: Optional[OrderStatus] = None,
    session: Session = Depends(get_session)
):
    statement = select(Order).where(Order.business_id == business_id)
    if status:
        statement = statement.where(Order.status == status)
    orders = session.exec(statement).all()
    return orders

@app.patch("/orders/{order_id}/status", response_model=Order)
def update_order_status(
    order_id: uuid.UUID,
    status: OrderStatus,
    session: Session = Depends(get_session)
):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


# --- CONVERSATIONS ---
@app.get("/businesses/{business_id}/conversations", response_model=List[ConversationRead])
def read_conversations(business_id: uuid.UUID, session: Session = Depends(get_session)):
    statement = select(Conversation).where(Conversation.business_id == business_id).order_by(Conversation.updated_at.desc())
    conversations = session.exec(statement).all()
    
    results = []
    for conv in conversations:
        client = conv.client
        results.append(ConversationRead(
            **conv.model_dump(),
            client_name=client.full_name or client.wa_id,
            client_wa_id=client.wa_id
        ))
    return results

@app.get("/businesses/{business_id}/conversations/client/{client_id}", response_model=ConversationRead)
def get_or_create_conversation(business_id: uuid.UUID, client_id: uuid.UUID, session: Session = Depends(get_session)):
    statement = select(Conversation).where(Conversation.business_id == business_id, Conversation.client_id == client_id)
    conversation = session.exec(statement).first()
    
    if not conversation:
        conversation = Conversation(business_id=business_id, client_id=client_id)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
    
    client = conversation.client
    return ConversationRead(
        **conversation.model_dump(),
        client_name=client.full_name or client.wa_id,
        client_wa_id=client.wa_id
    )

@app.get("/conversations/{conversation_id}/messages", response_model=List[MessageRead])
def read_messages(conversation_id: uuid.UUID, session: Session = Depends(get_session)):
    statement = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
    messages = session.exec(statement).all()
    return messages

@app.post("/conversations/{conversation_id}/messages", response_model=MessageRead)
def create_message(
    conversation_id: uuid.UUID,
    message: Message,
    session: Session = Depends(get_session)
):
    message.conversation_id = conversation_id
    session.add(message)
    
    # Update conversation's last message and updated_at
    conversation = session.get(Conversation, conversation_id)
    if conversation:
        conversation.last_message = message.content
        session.add(conversation)
        
        # If the manager is sending a message (SenderType.business), 
        # trigger the WhatsApp send via the channels service.
        if message.sender_type == SenderType.business:
            client = conversation.client
            if client and client.wa_id:
                try:
                    # Using a simple synchronous post for now as the endpoint is def
                    with httpx.Client() as http_client:
                        http_client.post(
                            f"{CHANNELS_API_URL}/send-message",
                            params={"phone_number": client.wa_id, "content": message.content},
                            timeout=10.0
                        )
                except Exception as e:
                    print(f"Error sending WhatsApp message via channels: {e}")
    
    session.commit()
    session.refresh(message)
    return message