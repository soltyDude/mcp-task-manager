# mcp-task-manager

A task management server built on Anthropic's [Model Context Protocol](https://modelcontextprotocol.io). Connects to Claude Desktop and lets you manage tasks through natural language — no UI, no backend, just Python and SQLite.

> "Create a high-priority task for fixing the auth bug, due Friday" → task created.  
> "What should I focus on today?" → returns overdue + urgent + high-priority tasks.

---

## How it works

MCP servers run as a local subprocess. Claude Desktop communicates with the server over stdin/stdout (JSON-RPC). When you type a request, Claude decides which tool to call, passes the parameters, and returns the result as a natural language response.
Claude Desktop  ──── JSON-RPC (stdio) ────  server.py (FastMCP)
│
TaskRepository
│
tasks.db (SQLite)

## Tools

| Tool | What it does |
|------|-------------|
| `create_task` | Create task with title, priority, due date, tags |
| `list_tasks` | List tasks, filter by status or priority |
| `get_task` | Get task by ID |
| `update_task` | Update any field |
| `complete_task` | Mark as completed |
| `delete_task` | Delete a task |
| `search_tasks` | Full-text search across title, description, tags |
| `get_summary` | Counts by status/priority + overdue |
| `plan_day` | Prioritized focus list for today |

## Setup

git clone / venv / pip install -e . / cp .env.example .env


## Stack
- Python 3.11+, FastMCP, SQLite, Pydantic v2