import os
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents.llm_agent import Agent
from google.adk import Runner

agent = Agent(
    name='test_agent', 
    model='gemini-2.5-flash', 
    instruction='You are a helpful assistant.', 
    tools=[]
)

from google.adk.sessions.in_memory_session_service import InMemorySessionService

runner = Runner(agent=agent, app_name='test', session_service=InMemorySessionService(), auto_create_session=True)
from google.genai import types

response_generator = runner.run(
    new_message=types.Content(role='user', parts=[types.Part.from_text(text="Say hello")]),
    user_id="test_user", 
    session_id="session1"
)

# It yields Event objects
for event in response_generator:
    if event.content:
        print(f"Content: {event.content}")
    else:
        print(f"Event: {event}")
