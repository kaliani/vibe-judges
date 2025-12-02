from fastapi import FastAPI
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from .graph import get_graph

graph = None


class ChatInput(BaseModel):
    messages: list[str]
    thread_id: str = Field(default="001")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    global graph
    graph = await get_graph()
    print("Graph agent initialized")

    yield 

    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat(payload: ChatInput):
    
    config = {"configurable": {"thread_id": payload.thread_id}}
    response = await graph.ainvoke({"messages": payload.messages}, config=config)
    return response["messages"][-1].content