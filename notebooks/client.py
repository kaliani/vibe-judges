# Create server parameters for stdio connection
from mcp import ClientSession, StdioServerParameters
from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
# Set your OpenAI API key here
api_key = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=api_key)

mcp_config = {
    "postgres": {
        "transport": "sse",
        "url": "http://127.0.0.1:8000/sse"   # зверни увагу на /sse
    }
}

async def run_agent():
        
        client = MultiServerMCPClient(mcp_config)

        async with client.session("postgres") as session:
              tools = await load_mcp_tools(session)
              model = ChatOpenAI(model="gpt-4o")
              agent = create_react_agent(model, tools)

              resp = await agent.ainvoke({"messages": "які поля є в таблиці documents?"})
              print(resp)

# Run the async function
if __name__ == "__main__":
    result = asyncio.run(run_agent())
    print(result)