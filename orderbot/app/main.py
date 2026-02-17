from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.team import order_agent_builder, compile_agent

load_dotenv(override=True)

from app.schemas import MessageRequest, ChatResponse
from app.schemas import MessageRequest, ChatResponse

@asynccontextmanager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Postgres connection pool
    async with AsyncConnectionPool(
        # Use DATABASE_URL or fallback to SUPABASE_URL if formatted correctly for postgres
        conninfo=os.getenv("DATABASE_URL", os.getenv("SUPABASE_URL")),
        max_size=20,
        kwargs={"autocommit": True}
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        
        # NOTE: you need to call .setup() the first time you're using your checkpointer
        await checkpointer.setup()
        
        app.state.order_agent = compile_agent(order_agent_builder, checkpointer)
        yield

app = FastAPI(title="OrderBot API", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "OrderBot API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: MessageRequest):
    try:
        # Prepare the input for the agent
        # The agent expects {"messages": [...], "user": {...}} in state
        user_state = {
            "phone_number": request.user.phone_number,
            "business_phone_number": request.user.business_phone_number,
        }
        if request.user.name is not None:
            user_state["name"] = request.user.name
        if request.user.items:
            user_state["items"] = request.user.items

        input_state = {
            "messages": [{"role": "user", "content": request.message}],
            "user": user_state
        }
        
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # Invoke the agent
        result = await request.app.state.order_agent.ainvoke(input_state, config)
        
        # Extract response
        # The result state contains "messages", the last one should be the bot's reply
        messages = result.get("messages", [])
        if not messages:
            return ChatResponse(message="No response from agent")
            
        last_message = messages[-1]
        if isinstance(last_message.content, str):
            response_text = last_message.content
        elif isinstance(last_message.content, list) and len(last_message.content) > 0:
            if isinstance(last_message.content[0], dict) and "text" in last_message.content[0]:
                response_text = last_message.content[0]["text"]
            else:
                response_text = str(last_message.content[0])
        else:
            response_text = str(last_message.content)
        print(response_text)
        image_path = result.get("image_path")
        print(response_text)
        
        return ChatResponse(message=response_text, image_path=image_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
