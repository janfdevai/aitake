import sys
sys.path.append('.')
import asyncio
from dotenv import load_dotenv

load_dotenv(override=True)

from agentevals.trajectory.llm import (
    TRAJECTORY_ACCURACY_PROMPT,
    create_trajectory_llm_as_judge,
)
from langsmith import Client

from app.order_agent.agent import orderbot_agent

client = Client()

trajectory_evaluator = create_trajectory_llm_as_judge(
    model="openai:gpt-5-nano",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)


async def run_agent(inputs):
    """Your agent function that returns trajectory messages."""
    print("\ntesting..", end="")

    # Our new ADK agent doesn't take raw "inputs" state dictionaries.
    # We must adapt the LangSmith dataset inputs to our process_message signature.
    # We assume 'inputs' is a dict matching the older structure.
    
    # Extract message from the LangGraph input structure
    messages_in_dataset = inputs.get("messages", [])
    if isinstance(messages_in_dataset, list) and len(messages_in_dataset) > 0:
        latest_message = messages_in_dataset[-1].get("content", "") if isinstance(messages_in_dataset[-1], dict) else getattr(messages_in_dataset[-1], "content", "")
    else:
        latest_message = str(messages_in_dataset)
        
    user_data = inputs.get("user", {})
    phone_number = user_data.get("phone_number", "test_user")
    business_phone = user_data.get("business_phone_number", "test_business")
    name = user_data.get("name", "Test User")

    # Run the agent
    response_text = orderbot_agent.process_message(
        message=latest_message,
        user_phone=phone_number,
        business_phone=business_phone,
        name=name
    )

    # To satisfy LangSmith evaluate, we need to return an output format it understands.
    # The trajectory evaluator typically expects to see a history of messages.
    # Since our ADK wrapper doesn't currently easily yield the whole trajectory (internal to ADK Chat),
    # we return the final assistant message for standard evaluators.
    return {"messages": [{"role": "assistant", "content": response_text}]}


async def main():
    await client.aevaluate(
        run_agent, data="whatsapp-ai-chatbot", evaluators=[trajectory_evaluator]
    )

if __name__ == "__main__":
    asyncio.run(main())
