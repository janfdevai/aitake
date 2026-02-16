
import sys
import os
from unittest.mock import MagicMock

# Add app to path
sys.path.append(os.getcwd())

# 1. Mock supabase_client module structure
mock_supabase_mod = MagicMock()
sys.modules["app.supabase_client"] = mock_supabase_mod

# 2. Mock google.genai
mock_genai_mod = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = mock_genai_mod

# 3. Import tools
# Note: Since we mocked app.supabase_client, the import inside tools.py will likely work or use the mock
try:
    from app.order_agent.tools import add_order_item, get_order_summary, add_order
    from app.order_agent.utils import merge_user
    import app.order_agent.tools as tools_module
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

# 4. Patch internal helpers in tools.py to avoid DB calls
def mock_get_business_id(phone):
    return "biz_123"

def mock_get_menu_items(bid):
    return [
        {"item_id": "1", "name": "Pizza", "price": 10.0},
        {"item_id": "2", "name": "Taco", "price": 2.0},
        {"item_id": "3", "name": "Hamburger", "price": 5.0}
    ]

tools_module._get_business_id = mock_get_business_id
tools_module._get_menu_items = mock_get_menu_items

# 5. Runtime Mock
class MockRuntime:
    def __init__(self, state):
        self.state = state
        self.tool_call_id = "test_call_id"

def run_test():
    print("--- Starting Reproduction Test ---")
    
    # Initial state
    state = {
        "user": {
            "business_phone_number": "123",
            "phone_number": "456",
            "name": "Test User",
            "items": []
        }
    }
    
    # ---------------------------------------------------------
    # Scenario: 
    # 1. User adds items (Turns 1-3)
    # 2. Agent checks summary (Turn 4) -> Sees correct total
    # 3. Agent mistakenly re-adds everything + checks summary (Turn 5)
    # 4. Agent places order (Turn 6) -> Sees doubled total
    # ---------------------------------------------------------
    
    print("\n--- Turns 1-3: Adding initial items ---")
    # Add Pizza (2)
    res = add_order_item.func("Pizza", 2, MockRuntime(state))
    state["user"] = merge_user(state["user"], res.update["user"])
    
    # Add Taco (2)
    res = add_order_item.func("Taco", 2, MockRuntime(state))
    state["user"] = merge_user(state["user"], res.update["user"])
    
    # Add Hamburger (1)
    res = add_order_item.func("Hamburger", 1, MockRuntime(state))
    state["user"] = merge_user(state["user"], res.update["user"])
    
    print(f"State after initial adds: {state['user']['items']}")
    
    # Calculate expected total
    # Pizza: 2 * 10 = 20
    # Taco: 2 * 2 = 4
    # Burger: 1 * 5 = 5
    # Total: 29
    
    print("\n--- Turn 4: Check Summary ---")
    summary = get_order_summary.func(MockRuntime(state))
    print(summary)
    if "$29.00" in summary:
        print(">> Summary is CORRECT ($29.00)")
    else:
        print(">> Summary is INCORRECT")

    print("\n--- Turn 5: The Agent Re-adds Items + Checks Summary ---")
    # In a single turn, the agent calls multiple tools.
    # Crucially, the 'state' passed to each tool is the SAME (the state at start of turn).
    # The updates are applied AFTER the tools run.
    
    turn_start_state = state.copy() # Shallow copy is enough for dict structure, but deeper for safety
    # Actually state structure: {'user': {'items': [...]}}
    # Deep copy items to simulate true snapshot
    import copy
    turn_start_state = copy.deepcopy(state)
    
    # Tool 1: re-add Pizza
    cmd1 = add_order_item.func("Pizza", 2, MockRuntime(turn_start_state))
    
    # Tool 2: re-add Taco
    cmd2 = add_order_item.func("Taco", 2, MockRuntime(turn_start_state))
    
    # Tool 3: re-add Hamburger
    cmd3 = add_order_item.func("Hamburger", 1, MockRuntime(turn_start_state))
    
    # Tool 4: check summary
    # Critically, it reads from turn_start_state!
    summary_turn5 = get_order_summary.func(MockRuntime(turn_start_state))
    print(f"Summary in Turn 5 (Parallel): \n{summary_turn5}")
    
    if "$29.00" in summary_turn5:
        print(">> Summary in Turn 5 shows $29.00 (Old State) - This explains why Agent thinks it's fine")
    else:
        print(f">> Summary in Turn 5 shows unexpected value")
        
    # Now verify the state UPDATE at end of Turn 5
    print("\nApplying updates from Turn 5...")
    state["user"] = merge_user(state["user"], cmd1.update["user"])
    state["user"] = merge_user(state["user"], cmd2.update["user"])
    state["user"] = merge_user(state["user"], cmd3.update["user"])
    
    print(f"State after Turn 5 updates: {state['user']['items']}")
    
    # Verify quantities
    # Should be 4, 4, 2
    items = state["user"]["items"]
    q_pizza = next(i for i in items if i["name"]=="Pizza")["quantity"]
    print(f"Pizza Quantity: {q_pizza}")
    
    if q_pizza == 4:
        print(">> DOUBLE COUNT CONFIRMED: Quantity is now 4 (Expected 2 if idempotent, but wait...)")
        print(">> The issue is that the agent re-added items thinking they were missing.")

    print("\n--- Turn 6: Place Order ---")
    # Mock supabase insert return
    mock_insert = MagicMock()
    mock_insert.data = [{"order_id": "new_order_uuid", "status": "pending"}]
    mock_supabase_mod.supabase.table().insert().execute.return_value = mock_insert
    
    # Mock client find
    mock_select = MagicMock()
    mock_select.data = [{"client_id": "client_uuid"}]
    mock_supabase_mod.supabase.table().select().eq().eq().execute.return_value = mock_select
    
    final_res = add_order.func("pickup", None, MockRuntime(state))
    
    if hasattr(final_res, "update"):
        msg = final_res.update["messages"][0].content
        print(f"Final Order Output:\n{msg}")
        if "$58.00" in msg:
             print(">> SUCCESS: Reproduced $58.00 Total")
    else:
        print(f"Final Result: {final_res}")

if __name__ == "__main__":
    run_test()
