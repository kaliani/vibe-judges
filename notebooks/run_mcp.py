import asyncio
import os
# Імпортуємо нативні класи MCP (без обгорток LangChain)
from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client

async def run_chroma_mcp():
    # 1. Параметри (ті самі, що й раніше)
    server_params = StdioServerParameters(
        command="uvx",  # Переконайтеся, що uv встановлено
        args=["chroma-mcp-server"],
        env={
            "CHROMA_CLIENT_TYPE": "http",
            "CHROMA_SERVER_HOST": "localhost",
            "CHROMA_SERVER_HTTP_PORT": "8000",
            "CHROMA_API_IMPL": "rest",
            # Додаємо PATH, щоб python міг знайти uvx, якщо він не в стандартному місці
            "PATH": os.environ.get("PATH") 
        }
    )

    print("🔌 Підключення до процесу MCP...")
    
    # 2. Використовуємо контекстний менеджер (стандартний патерн MCP)
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Ініціалізація протоколу
                await session.initialize()
                
                # 3. Отримання інструментів
                print("🔍 Опитування доступних інструментів...")
                tools_result = await session.list_tools()
                
                print(f"\n✅ Успішно! Знайдено {len(tools_result.tools)} інструментів:")
                for tool in tools_result.tools:
                    print(f" - {tool.name}")
                    
                # Якщо треба побачити деталі першого інструменту:
                # print(tools_result.tools[0])

    except FileNotFoundError:
        print("❌ Помилка: Не знайдено команду 'uvx'. Спробуйте 'pip install uv' або змініть command на 'python'.")
    except Exception as e:
        print(f"❌ Сталася помилка: {e}")

if __name__ == "__main__":
    asyncio.run(run_chroma_mcp())