from fastapi import FastAPI
from pydantic import BaseModel, Field
from .graph import get_graph


graph = get_graph()

app = FastAPI()


class ChatInput(BaseModel):
    messages: list[str]
    thread_id: str = Field(default="001")

@app.post("/chat")
async def chat(payload: ChatInput):
    
    config = {"configurable": {"thread_id": payload.thread_id}}
    response = await graph.ainvoke({"messages": payload.messages}, config=config)
    return response["messages"][-1].content