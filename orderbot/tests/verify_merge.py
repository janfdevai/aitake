
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.order_agent.utils import merge_cart

current_items = [{"item_id": "1", "quantity": 1, "name": "Pizza", "price": 10.0}]
new_items = []

result = merge_cart(current_items, new_items)
print(f"Current: {current_items}")
print(f"New: {new_items}")
print(f"Result: {result}")

if result == []:
    print("Confirmed: Empty list clears the cart.")
else:
    print("Result is not empty.")
