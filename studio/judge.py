import os
import asyncio
from dotenv import load_dotenv

import requests
from striprtf.striprtf import rtf_to_text

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

model = ChatOpenAI(model="gpt-4.1-mini", temperature=0)




mcp_config = {
    "postgres": {
        "transport": "sse",
        "url": "http://127.0.0.1:8000/sse" 
    }
}

_client = None
_graph = None  # кешований екземпляр агента для повторного використання

def get_mcp_client():
    """Get or initialize MCP client lazily to avoid issues with LangGraph Platform."""
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

general_prompt = """
<Task>
You are a helpful assistant. You can analyse summarize texts (court cases) and run computations with provided tools
Please respond in Ukrainian.
</Task>

<Available Tools>      
You have access to postgres database (database: mydb, schema: public):
 - list_schemas: List all schemas in the database
 - list_objects: List objects in a schema
 - get_object_details: Show detailed information about a database object
 - explain_query: Explains the execution plan for a SQL query, showing how the database will execute it and provides detailed cost estimates
 - analyze_workload_indexes: Analyze frequently executed queries in the database and recommend optimal indexes
 - analyze_query_indexes: Analyze a list of (up to 10) SQL queries and recommend optimal indexes
 - analyze_db_health: Analyzes database health. Here are the available health checks:\n- index - checks for invalid, duplicate, and bloated indexes\n- connection - checks the number of connection and their utilization\n- vacuum - checks vacuum health for transaction id wraparound\n- sequence - checks sequences at risk of exceeding their maximum value\n- replication - checks replication health including lag and slots\n- buffer - checks for buffer cache hit rates for indexes and tables\n- constraint - checks for invalid constraints\n- all - runs all checks\nYou can optionally specify a single health check or a comma-separated list of health checks. The default is 'all' checks.
 - get_top_queries: Reports the slowest or most resource-intensive queries using data from the 'pg_stat_statements
 - execute_sql: Execute a read-only SQL query
 - extract_rtf_text: Download an RTF document from the given URL and extract plain text from it
</Available Tools> 

<Database Schema Overview>
Below is an overview of the most important tables available in the database. Use these descriptions to generate more accurate SQL queries.
    TABLE: cause_categories
    DESCRIPTION: Reference table containing categories of legal causes (e.g., civil, criminal, administrative). Used for classifying court cases by type of legal dispute.

    TABLE: courts
    DESCRIPTION: Directory of courts. Stores court names, jurisdiction level, location, region, and related metadata.

    TABLE: documents
    DESCRIPTION: Metadata for case-related documents (RTF/PDF). Includes URLs, document types, upload dates, and links to associated cases.

    TABLE: instances
    DESCRIPTION: Contains information about court instances (e.g., first instance, appellate, supreme). Used to identify the level at which a case is being reviewed.

    TABLE: judges
    DESCRIPTION: Contains judge profiles with names, positions, court affiliations, and unique identifiers for linking judges to decisions or hearings.

    TABLE: judgment_forms
    DESCRIPTION: Reference table describing forms of judgments (e.g., ruling, decision, order). Helps classify the outcome type of a case.

    TABLE: justice_kinds
    DESCRIPTION: Contains categories of justice types (e.g., administrative justice, civil justice, criminal justice). Used to categorize cases by their legal system branch.

    TABLE: regions
    DESCRIPTION: Stores geographical regions and territorial units. Used for mapping courts, cases, and events to specific areas.
</Database Schema Overview>
"""

async def get_graph():
    """
    Отримати (та закешувати) граф-агент для судових задач.
    Використовуй у будь-якому асинхронному оточенні, включно з багатoагентними пайплайнами.
    """
    global _graph
    if _graph is not None:
        return _graph

    tools = await get_all_tools()

    _graph = create_agent(
        model,
        tools,
        system_prompt=general_prompt      
    )
    return _graph


def get_graph_sync():
    """
    Синхронний доступ до агента.
    - Використовуй лише там, де НІЯКОГО поточного event loop немає (наприклад, простий CLI).
    - У серверах / фреймворках з уже запущеним loop -> викликай await get_graph().
    """
    try:
        # Якщо тут вже є активний event loop — забороняємо синхронний виклик
        asyncio.get_running_loop()
    except RuntimeError:
        # Немає активного loop — можна безпечно виконати через asyncio.run
        return asyncio.run(get_graph())
    else:
        raise RuntimeError(
            "get_graph_sync() не можна викликати всередині наявного event loop; "
            "використай `await get_graph()`."
        )


# Сам граф, який очікує LangGraph Platform (повинен називатися саме `graph`)
# Створюється один раз синхронно при імпорті модуля в окремому потоці runtime'у.
graph = get_graph_sync()


async def run_judge(messages):
    """
    Виклик агента як підграфа з іншого пайплайна/агента.
    Очікує список повідомлень LangGraph/LangChain формату.
    """
    agent = await get_graph()
    return await agent.ainvoke({"messages": messages})


@tool("judge_agent")
async def judge_agent_tool(messages: list) -> str:
    """
    Tool-обгортка для виклику цього судового агента з інших агентів.
    Очікує messages (list of dict/BaseMessage); повертає сирий результат агента.
    """
    result = await run_judge(messages)
    return result


if __name__ == "__main__":
    async def _demo():
        """
        Простий інтерактивний режим для швидкого тесту агента.
        """
        graph = await get_graph()
        print("AI-агент запущений. Введи запит українською (або 'exit'/'quit' для виходу).")
        while True:
            query = input("> ").strip()
            if query.lower() in {"exit", "quit"}:
                break

            result = await graph.ainvoke({"messages": [query]})
            print("\nВідповідь агента:\n")
            print(result)
            print("\n" + "-" * 50 + "\n")

    asyncio.run(_demo())