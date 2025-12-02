import os
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from .tools import tools

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(model="gpt-4o", temperature=0)

def get_graph():

    agent = create_agent(
            model,
            tools,
            system_prompt="You are helpful assistant"       
    )

    return agent