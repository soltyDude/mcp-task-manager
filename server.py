import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context

from core import TaskRepository
from tools import (
    create_task, list_tasks, get_task, update_task,
    delete_task, complete_task, search_tasks, get_summary, plan_day,
)

load_dotenv()


@asynccontextmanager
async def lifespan(server: FastMCP):
    db_path = os.getenv("DATABASE_PATH", "tasks.db")
    repo = TaskRepository(db_path)
    print(f"✅ MCP Task Manager started — DB: {db_path}")
    yield {"repo": repo}
    print("🛑 MCP Task Manager stopped")


mcp = FastMCP(name=os.getenv("SERVER_NAME", "mcp-task-manager"), lifespan=lifespan)

mcp.tool()(create_task)
mcp.tool()(list_tasks)
mcp.tool()(get_task)
mcp.tool()(update_task)
mcp.tool()(delete_task)
mcp.tool()(complete_task)
mcp.tool()(search_tasks)
mcp.tool()(get_summary)
mcp.tool()(plan_day)

if __name__ == "__main__":
    mcp.run()
