from typing import Any, Optional

from google import genai

from app import PROJECT_ROOT

client = genai.Client()


def merge_cart(current_items: list[dict[str, Any]], new_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merges new items into the current cart.
    
    If new_items is empty, it clears the cart (or init).
    If new_items has items, it merges them by item_id, summing quantities.
    """
    if not new_items:
        # If explicitly setting empty list, we clear the cart. 
        # However, we need to distinguish between "initially empty" and "clearing".
        # For this specific racer condition fix, we assume the tool returns a DELTA.
        # But if the tool returns a full empty list to clear, we should respect that.
        # Let's assume an empty list from the tool means "clear cart" or "no change" depending on context?
        # Actually, in the `add_order` tool, we return `{"items": []}` to clear. 
        # In `add_order_item`, we will return `{"items": [item]}`.
        # So:
        # - If input is [], it's a clear signal.
        # - If input is [item], it's a delta.
        return []

    # Deep copy current items to avoid mutating state in place if that matters
    merged = {item["item_id"]: item.copy() for item in current_items}

    for new_item in new_items:
        item_id = new_item.get("item_id")
        if item_id in merged:
            # Update quantity
            merged[item_id]["quantity"] += new_item.get("quantity", 0)
        else:
            # Add new item
            merged[item_id] = new_item.copy()

    # Filter out zero or negative quantities
    return [item for item in merged.values() if item["quantity"] > 0]


def merge_user(
    left: Optional[dict[str, Any]], right: Optional[dict[str, Any]]
) -> dict[str, Any]:
    """Reducer to merge user state updates."""
    if left is None:
        return right or {}
    if right is None:
        return left
    
    # Start with a shallow copy of left
    merged = left.copy()
    
    # Update simple fields
    for key, value in right.items():
        if key == "items" and isinstance(value, list):
            # Special handling for items
            merged["items"] = merge_cart(left.get("items", []), value)
        else:
            merged[key] = value
            
    return merged


def generate_weather_image(city: str, weather: str):
    prompt = f"Create a picture of the city of {city} with the weather {weather}"
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt],
    )

    for part in response.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = part.as_image()
            image.save(f"{PROJECT_ROOT}/public/weather_image.png")
