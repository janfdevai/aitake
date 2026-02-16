
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

# Mock app.supabase_client BEFORE importing tools
mock_supabase_client_module = MagicMock()
sys.modules["app.supabase_client"] = mock_supabase_client_module

# Mock google.genai BEFORE importing utils
mock_genai_module = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = mock_genai_module

import app.order_agent.tools as tools_module
from app.order_agent.tools import add_order_item
from app.order_agent.utils import merge_user
from app.order_agent.tools import add_order_item
from app.order_agent.utils import merge_user

# Mock Runtime
class MockRuntime:
    def __init__(self, state):
        self.state = state
        self.tool_call_id = "test_id"

# Mock data
mock_menu = [
    {"item_id": "1", "name": "Burger", "price": 10.0},
    {"item_id": "2", "name": "Fries", "price": 5.0}
]

def mock_get_menu_items(business_id):
    return mock_menu

def mock_get_business_id(phone):
    return "biz_123"

# Patch the helpers
tools_module._get_menu_items = mock_get_menu_items
tools_module._get_business_id = mock_get_business_id

# Mock supabase to avoid import errors if strictly needed, but we patched the helpers directly.
# However, `app.order_agent.tools` imports `supabase` at top level. 
# If `app.supabase_client` fails to import, we might have issues.
# Assuming UV environment has dependencies installed.

def test_parallel_calls():
    print("Testing parallel tool calls with DELTA updates...")
    
    # Initial State (Empty cart)
    initial_state = {
        "user": {
            "business_phone_number": "123",
            "items": []
        }
    }
    
    # Tool 1: Add Burger
    # Note: Runtime state is mostly irrelevant for the NEW implementation 
    # except for getting phone number.
    runtime1 = MockRuntime(initial_state) 
    # add_order_item is a StructuredTool. We need to call the underlying function to test logic directly.
    # The @tool decorator stores the original function in .func (usually).
    # If not, we might need to check Langchain version, but .func is standard.
    try:
        func = add_order_item.func
    except AttributeError:
        # Fallback if .func is not available (unlikely with standard @tool)
        print("Could not access underlying function of tool.")
        return

    result1 = func(product_name="Burger", quantity=1, runtime=runtime1)
    
    # Tool 2: Add Fries
    runtime2 = MockRuntime(initial_state) 
    result2 = func(product_name="Fries", quantity=1, runtime=runtime2)
    
    if isinstance(result1, str) or isinstance(result2, str):
        print(f"Error in tools: {result1} / {result2}")
        return

    # Extract updates
    update1 = result1.update["user"]
    update2 = result2.update["user"]
    
    print(f"Update 1: {update1}")
    print(f"Update 2: {update2}")
    
    # Verify updates are Deltas (lists of length 1)
    if len(update1["items"]) != 1 or len(update2["items"]) != 1:
        print("FAILURE: Tools are not returning deltas.")
        return

    # Simulate State Merge (Sequential application of parallel results)
    
    # Apply Update 1
    state_after_1 = merge_user(initial_state["user"], update1)
    print(f"State after 1: {state_after_1.get('items')}")
    
    # Apply Update 2 (on top of state_after_1)
    # This is the crux: merge_user must perform the list merge, not overwrite.
    final_state_user = merge_user(state_after_1, update2)
    
    print(f"Final Cart: {final_state_user.get('items')}")
    
    # Check
    items = final_state_user.get("items", [])
    has_burger = any(i["name"] == "Burger" for i in items)
    has_fries = any(i["name"] == "Fries" for i in items)
    
    if has_burger and has_fries:
        print("SUCCESS: Both items present. Race condition fixed.")
    else:
        print("FAILURE: Items missing.")

if __name__ == "__main__":
    test_parallel_calls()
