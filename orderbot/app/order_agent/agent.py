import os
from google.adk.agents.llm_agent import Agent
from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from typing import Dict, Optional, Callable

from app.order_agent.session import SessionState
from app.order_agent.tools import (
    get_user_phone_number,
    get_user_name,
    update_user_name,
    get_menu,
    add_order_item,
    add_order,
    get_order_summary
)

class OrderbotADKAgent:
    def __init__(self):
        self.model_name = "gemini-3-flash-preview"
        self._sessions: Dict[str, SessionState] = {}
        self._agents: Dict[str, Agent] = {}
        self._session_service = InMemorySessionService()
        
        self.system_instruction = """You are OrderBot, an automated assistant for taking restaurant orders.

Your responsibilities:
- Greet the customer in a friendly, casual way based on their name if you know it, otherwise ask for it.
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

    def get_or_create_session(self, user_phone: str, business_phone: str, name: str = "Unknown") -> SessionState:
        session_id = f"{business_phone}:{user_phone}"
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(
                user_id=session_id,
                phone_number=user_phone,
                business_phone_number=business_phone,
                name=name
            )
        return self._sessions[session_id]

    def _get_agent(self, session: SessionState) -> Agent:
        if session.user_id not in self._agents:
            # We must bind the session object to the tools.
            # ADK supports callable objects as tools.
            tools = [
                self._bind_tool(get_user_phone_number, session),
                self._bind_tool(get_user_name, session),
                self._bind_tool(update_user_name, session),
                self._bind_tool(get_menu, session),
                self._bind_tool(add_order_item, session),
                self._bind_tool(add_order, session),
                self._bind_tool(get_order_summary, session)
            ]
            
            # ADK uses `Agent(...)` which initializes the generative model under the hood.
            chat_agent = Agent(
                model=self.model_name,
                name='orderbot_agent',
                description="Takes restaurant orders from users via chat.",
                instruction=self.system_instruction,
                tools=tools
            )
            self._agents[session.user_id] = chat_agent
            
        return self._agents[session.user_id]
        
    def _bind_tool(self, func: Callable, session: SessionState) -> Callable:
        """Helper to create a wrapped function that injects the session."""
        import inspect
        from functools import wraps
        
        sig = inspect.signature(func)
        parameters = list(sig.parameters.values())
        
        # Remove 'session' from the parameters exposed to the LLM
        new_params = [p for p in parameters if p.name != 'session']
        new_sig = sig.replace(parameters=new_params)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, session=session, **kwargs)
            
        wrapper.__signature__ = new_sig # ADK/Pydantic uses signature to generate schema
        return wrapper

    def process_message(self, message: str, user_phone: str, business_phone: str, name: str = "Unknown", image_path: Optional[str] = None) -> str:
        """Main entry point to talk to the agent."""
        session = self.get_or_create_session(user_phone, business_phone, name)
        
        # Get the ADK Agent instance for this session
        agent = self._get_agent(session)
        
        runner = Runner(
            agent=agent, 
            app_name='orderbot', 
            session_service=self._session_service, 
            auto_create_session=True
        )
        
        contents = []
        if image_path and os.path.exists(image_path):
             # Skipping file logic for now unless requested
             pass
        else:
             contents.append(types.Part.from_text(text=message))
             
        new_message = types.Content(role='user', parts=contents)
        
        response_generator = runner.run(
            new_message=new_message,
            user_id=session.user_id,
            session_id=session.user_id
        )
        
        # ADK runner yields events. We concatenate assistant content.
        final_text = []
        for event in response_generator:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text.append(part.text)
                        
        return "".join(final_text)

# Global agent instance
orderbot_agent = OrderbotADKAgent()
