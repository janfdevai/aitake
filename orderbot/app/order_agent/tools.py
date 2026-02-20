from typing import Optional, Dict, Any, List
from app.supabase_client import supabase
from app.order_agent.session import SessionState, OrderItem

# Business resolution helper
def _get_business_id(phone_number: str) -> Optional[str]:
    """Helper to resolve business UUID from phone number."""
    try:
        response = supabase.table("businesses").select("business_id").eq("whatsapp_phone_number", phone_number).execute()
        if response.data:
            return response.data[0].get("business_id")
        return None
    except Exception as e:
        print(f"Error fetching business ID from Supabase: {e}")
        return None

def _get_menu_items(business_id: str) -> List[Dict[str, Any]]:
    try:
        # Note: 'menu_items' table uses 'item_id', 'name', 'price', etc.
        response = supabase.table("menu_items").select("*").eq("business_id", business_id).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching menu from Supabase: {e}")
        return []

def get_user_phone_number(session: SessionState) -> str:
    """Get the user's phone number."""
    return session.phone_number

def get_user_name(session: SessionState) -> str:
    """Get the name of the user"""
    return session.name

def update_user_name(user_name: str, session: SessionState) -> str:
    """Update the name of the user in the state once they've revealed it."""
    session.name = user_name
    return "Successfully updated user name"

def get_menu(session: SessionState) -> str:
    """Get the menu for the business the user is interacting with."""
    business_phone = session.business_phone_number
    if not business_phone:
        return "Error: Business phone number not found in session."

    business_id = _get_business_id(business_phone)
    if not business_id:
        return "Error: Could not find business associated with this phone number."

    items = _get_menu_items(business_id)
    if not items:
        return "The menu is currently empty."

    menu_str = "Welcome to our menu!\n\n"
    
    for item in items:
        price = float(item.get("price", 0))
        name = item.get("name")
        desc = item.get("description")
        
        menu_str += f"- {name}: ${price:.2f}"
        if desc:
            menu_str += f" ({desc})"
        menu_str += "\n"

    return menu_str

def add_order_item(
    product_name: str, quantity: int, session: SessionState
) -> str:
    """Add an item to the user's current order (cart)."""
    business_phone = session.business_phone_number

    if not business_phone:
        return "Error: Business phone number not found in session."

    business_id = _get_business_id(business_phone)
    if not business_id:
        return "Error: Could not find business."

    items = _get_menu_items(business_id)
    
    # Find item by name (case-insensitive)
    target_item = None
    for item in items:
        if item.get("name", "").lower() == product_name.lower():
            target_item = item
            break
    
    if not target_item:
        # Try partial match
        matches = [i for i in items if product_name.lower() in i.get("name", "").lower()]
        if len(matches) == 1:
            target_item = matches[0]
        elif len(matches) > 1:
            names = ", ".join([m.get("name") for m in matches])
            return f"Multiple items found matching '{product_name}'. Please be more specific: {names}"
        else:
            return f"Item '{product_name}' not found on the menu."
    
    # Construct the order item
    order_item = OrderItem(
        item_id=target_item.get("item_id"),
        quantity=quantity,
        name=target_item.get("name"),
        price=float(target_item.get("price", 0))
    )

    session.add_item(order_item)

    return f"Added {quantity}x {target_item.get('name')} to your cart."

def add_order(delivery_type: str, address: str, session: SessionState) -> str:
    """
    Place the order.
    Args:
        delivery_type: 'pickup' or 'delivery'.
        address: Delivery address (required if delivery_type is 'delivery'). Set to 'None' if pickup.
    """
    business_phone = session.business_phone_number
    client_phone = session.phone_number
    client_name = session.name
    cart_items = session.items

    if not business_phone or not client_phone:
        return "Error: Missing business or client information."

    if not cart_items:
        return "Your cart is empty. Please add items before placing an order."

    if delivery_type.lower() == "delivery" and (not address or address == "None"):
        return "Error: Delivery address is required for delivery orders."

    # 1. Get Business ID
    business_id = _get_business_id(business_phone)
    if not business_id:
        return "Error: Could not resolve business ID."

    try:
        # 2. Get or Create Client
        client_id = None
        
        # Try to find client
        try:
            c_query = supabase.table("clients").select("client_id").eq("business_id", business_id).eq("wa_id", client_phone).execute()
            if c_query.data:
                client_id = c_query.data[0].get("client_id")
        except Exception as e:
            print(f"Error checking client: {e}")
            
        # If not found, create
        if not client_id:
            try:
                new_client = {
                    "business_id": business_id,
                    "wa_id": client_phone,
                    "full_name": client_name,
                    "phone_number": client_phone
                }
                c_insert = supabase.table("clients").insert(new_client).execute()
                if c_insert.data:
                    client_id = c_insert.data[0].get("client_id")
            except Exception as e:
                return f"Error creating client record in Supabase: {e}"

        if not client_id:
            return "Error: Failed to resolve client ID."

        # 3. Create Order
        total_amount = session.cart_total
        
        order_payload = {
            "business_id": business_id,
            "client_id": client_id,
            "delivery_type": delivery_type.lower(),
            "delivery_address": address if delivery_type.lower() == "delivery" else None,
            "total_amount": total_amount,
            "status": "pending"
        }
        
        order_insert = supabase.table("orders").insert(order_payload).execute()
        if not order_insert.data:
            return "Error: Failed to create order in Supabase."
            
        order_data = order_insert.data[0]
        order_uuid = order_data.get("order_id")

        # 4. Create Order Items
        items_payload = []
        for i in cart_items:
            items_payload.append({
                "order_id": order_uuid,
                "item_id": i.item_id,
                "quantity": i.quantity,
                "unit_price": i.price,
                "name_snapshot": i.name
            })
        
        if items_payload:
            supabase.table("order_items").insert(items_payload).execute()

        session.clear_cart()

        return f"Order placed successfully! Order ID: {order_uuid}\nTotal: ${total_amount:.2f}\nStatus: {order_data.get('status')}"

    except Exception as e:
        return f"Error placing order in Supabase: {e}"


def get_order_summary(session: SessionState) -> str:
    """Get the summary of the current order (cart)."""
    items = session.items
    if not items:
        return "Your cart is currently empty."

    summary = "Here is your current order summary:\n\n"
    total = session.cart_total

    for item in items:
        cost = item.price * item.quantity
        summary += f"- {item.name} (x{item.quantity}): ${cost:.2f}\n"

    summary += f"\nTotal: ${total:.2f}"
    return summary
