from langgraph.checkpoint.memory import InMemorySaver

from app.order_agent.graph import order_agent_builder


def compile_agent(builder, memory):
    """Compile the agent using the provided builder and memory"""
    return builder.compile(checkpointer=memory)


order_agent = compile_agent(order_agent_builder, InMemorySaver())
