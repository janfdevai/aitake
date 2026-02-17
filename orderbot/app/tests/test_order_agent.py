import asyncio
from dotenv import load_dotenv

load_dotenv(override=True)

from langgraph.checkpoint.memory import InMemorySaver

from agentevals.trajectory.llm import (
    TRAJECTORY_ACCURACY_PROMPT,
    create_trajectory_llm_as_judge,
)
from langsmith import Client

from app.team import order_agent_builder, compile_agent

# Initialize agent for testing with InMemorySaver
order_agent = compile_agent(order_agent_builder, InMemorySaver())

client = Client()

trajectory_evaluator = create_trajectory_llm_as_judge(
    model="openai:gpt-5-nano",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)


async def run_agent(inputs):
    """Your agent function that returns trajectory messages."""
    # print(f"DEBUG INPUTS: {inputs}")
    print("\ntesting..", end="")

    # Define the config required by the checkpointer
    config = {"configurable": {"thread_id": "eval-session"}}

    # Pass config as the second argument to invoke
    outputs = await order_agent.ainvoke(
        inputs,
        config=config,
    )

    # print(f"DEBUG OUTPUTS: {outputs}")

    return outputs


async def main():
    await client.aevaluate(
        run_agent, data="whatsapp-ai-chatbot", evaluators=[trajectory_evaluator]
    )


asyncio.run(main())

# uv run python -m app.agents.tests.test_order_agent
