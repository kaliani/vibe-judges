import os
from dotenv import load_dotenv
import requests
from langchain_core.tools import tool

from striprtf.striprtf import rtf_to_text

from langchain_openai import ChatOpenAI

from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(model="gpt-4o", temperature=0)


mcp_config = {
    "postgres": {
        "transport": "sse",
        "url": "http://127.0.0.1:8001/sse" 
    }
}

_client = None


def get_mcp_client():
    """Lazy init of MCP client (important for FastAPI)."""
    global _client
    if _client is None:
        _client = MultiServerMCPClient(mcp_config)
    return _client

@tool
def extract_rtf_text(url: str) -> str:
    """
    Download an RTF document from the given URL and extract plain text from it.
    """

    response = requests.get(url)
    response.raise_for_status()

    rtf_content = response.content.decode("utf-8", errors="ignore")

    text = rtf_to_text(rtf_content)
    return  text

async def load_mcp_tools():
    """
    Must be awaited inside FastAPI startup event.
    """
    client = get_mcp_client()
    mcp_tools = await client.get_tools()
    return mcp_tools

async def get_all_tools():
    """
    Returns merged list of:
    - MCP tools
    - Local Python tools
    """
    mcp_tools = await load_mcp_tools()
    local_tools = [extract_rtf_text]
    return mcp_tools + local_tools