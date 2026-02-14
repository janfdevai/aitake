from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import SystemMessage
from langgraph.prebuilt import ToolNode

from app.order_agent.state import MessagesState
from app.order_agent.tools import tools

model = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0)
model_with_tools = model.bind_tools(tools)


def llm_call(state: MessagesState):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="""You are OrderBot, an automated assistant for taking restaurant orders.

                                    Your responsibilities:
                                    - Greet the customer in a friendly, casual way.
                                    - Never list or describe the menu in the greeting.
                                    - Use `get_menu` only to understand what items and options exist.
                                    - Collect the customer’s order step by step.
                                    - For each item, clarify required options (size, extras, variations) so the item is uniquely identified.
                                    - Only offer items, options, and extras that exist in the menu. Never invent anything.
                                    - Add items using `add_order_item` only after the customer confirms them.
                                    - Ask whether the order is pickup or delivery.
                                    - If delivery, ask for the delivery address.
                                    - When the customer finishes ordering, summarize the order using `get_order_summary`.
                                    - Ask one final time if they want to add anything else.
                                    - Register the order using `add_order`.
                                    - Collect payment details last.
                                    - If the order is pickup:
                                    - Inform the customer that the pickup time is approximately **1–1:30 hours**.
                                    - Finish the conversation with a friendly closing such as: “See you soon.”
                                    - If the order is delivery:
                                    - Inform the customer that the delivery time is approximately **1:30–2 hours**.
                                    - Close the conversation in a friendly way.

                                    Conversation rules:
                                    - Be brief, friendly, and very conversational.
                                    - Ask only one question per response, when necessary.
                                    - Do not move to the next step until the current step is clearly confirmed.
                                    - Never offer suggestions or items that are not on the menu.


                                """
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
        "image_path": state.get("image_path", ""),
    }


tool_node = ToolNode(tools)
