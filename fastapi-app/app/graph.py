import os
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from .tools import get_all_tools
from .prompts import general_prompt

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

async def get_graph():
    
        model = ChatOpenAI(model="gpt-4o", temperature=0)
        tools = await get_all_tools()
        
        agent = create_agent(
            model,
            tools,
            system_prompt=general_prompt      
        )
        
        return agent