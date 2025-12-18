# agent.py
import os
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
# from langgraph.prebuilt import create_agent_executor
from langchain.agents import create_agent
from langserve import add_routes
from fastapi import FastAPI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    MessagesPlaceholder(variable_name="messages"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])
model = ChatOpenAI(temperature=0)
agent = {"messages": lambda x: x["messages"], "agent_scratchpad": lambda x: []} | prompt | model
app = create_agent(agent, [])
fastapi_app = FastAPI(title="LangGraph Agent")
add_routes(fastapi_app, app, path="/chat")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fastapi_app, host="localhost", port=2024)