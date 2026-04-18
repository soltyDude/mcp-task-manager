# mcp-task-manager

A local task manager that plugs into **Claude Desktop** through Anthropic's [Model Context Protocol](https://modelcontextprotocol.io). No UI, no backend service — just a Python process and a SQLite file. You manage tasks by talking to Claude.

> *"Create a high-priority task to fix the auth bug, due Friday, tag it backend."* → task created.
> *"What should I focus on today?"* → returns overdue + urgent + high-priority tasks.
> *"Mark task 3 completed and show me a summary."* → done + stats.

**Stack:** Python 3.11+ · FastMCP · SQLite · Pydantic v2
**Status:** working locally, 9 tools implemented

---

## Why this project

Built to learn MCP end-to-end: server lifecycle, tool registration, stdio transport, and how Claude picks tools from natural-language requests. It's a small but complete example — the kind of thing you'd extend into a real internal tool at work.

---

## How it works

MCP servers run as a local subprocess. Claude Desktop talks to the server over **stdio** using JSON-RPC. When you type a message, Claude:

1. Picks which registered tool fits the request
2. Fills in the parameters from your natural language
3. Calls the tool, gets back structured data (Pydantic models)
4. Summarises the result back to you in plain English

```
Claude Desktop  ──── JSON-RPC (stdio) ────  server.py  (FastMCP)
                                                │
                                         TaskRepository
                                                │
                                           tasks.db  (SQLite)
```

---

## Tools

| Tool            | What it does                                                   |
| --------------- | -------------------------------------------------------------- |
| `create_task`   | Create a task with title, description, priority, due date, tags |
| `list_tasks`    | List tasks, optionally filtered by status and/or priority      |
| `get_task`      | Fetch a single task by ID                                      |
| `update_task`   | Update any field (title, description, priority, status, due date, tags) |
| `complete_task` | Shortcut — mark as `completed`                                 |
| `delete_task`   | Delete a task by ID                                            |
| `search_tasks`  | Substring search across title, description, and tags           |
| `get_summary`   | Counts by status and priority + overdue count                  |
| `plan_day`      | Prioritised focus list for today (overdue + urgent + high)     |

Priorities: `low` · `medium` · `high` · `urgent`
Statuses: `pending` · `in_progress` · `completed` · `cancelled`

---

## Project structure

```
mcp-task-manager/
├── server.py           # FastMCP entry point, tool registration, lifespan
├── core/
│   ├── models.py       # Pydantic models + enums (Task, TaskCreate, TaskUpdate, TaskSummary)
│   └── repository.py   # SQLite DAO — CRUD, search, summary
├── tools/
│   └── __init__.py     # 9 MCP tool functions (thin layer over repository)
├── pyproject.toml
└── .env.example
```

Three layers, one responsibility each:

- **`tools/`** — the MCP-facing surface. Each function has a docstring that Claude reads to understand when/how to call it.
- **`core/repository.py`** — SQLite access. Raw SQL, indexed on `status`, `priority`, `due_date`.
- **`core/models.py`** — validation, serialization, enums.

---

## Setup

**Requirements:** Python 3.11+, [Claude Desktop](https://claude.ai/download).

```bash
git clone https://github.com/soltyDude/mcp-task-manager.git
cd mcp-task-manager

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e .
cp .env.example .env
```

### Connect to Claude Desktop

Open your Claude Desktop config:

- **macOS** — `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows** — `%APPDATA%\Claude\claude_desktop_config.json`

Add the server:

```json
{
  "mcpServers": {
    "mcp-task-manager": {
      "command": "/absolute/path/to/mcp-task-manager/.venv/bin/python",
      "args": ["/absolute/path/to/mcp-task-manager/server.py"]
    }
  }
}
```

Restart Claude Desktop. The tools will show up under the 🔌 icon.

### Configuration

`.env` supports two variables:

```
DATABASE_PATH=tasks.db       # where SQLite stores data
SERVER_NAME=mcp-task-manager # name shown in Claude Desktop
```

---

## Example session

```
You:    Add a task: refactor the auth filter, high priority, due tomorrow, tags: backend, security

Claude: Created task #1 — "Refactor the auth filter" (high, due 2025-04-19, tags: backend, security)

You:    What's my plan for today?

Claude: 📅 Day plan for 2025-04-18
        🔥 FOCUS (urgent + high priority)
          [1] [HIGH] Refactor the auth filter  #backend #security
        📊 Total: 1 | In progress: 0 | Overdue: 0

You:    Mark it in progress and show a summary

Claude: Task #1 updated — status: in_progress.
        📊 Total: 1 | Pending: 0 | In progress: 1 | Completed: 0 | Overdue: 0
```

---

## Design notes

A few choices worth calling out, in case you're reading this as a reviewer:

- **Lifespan-scoped repository.** The `TaskRepository` is built once in FastMCP's `lifespan` context manager and injected via `ctx.request_context.lifespan_context`. Tools stay stateless; the connection details don't leak into tool code.
- **Enums instead of magic strings.** `Priority` and `TaskStatus` are `str` enums — validated by Pydantic on input, stored as strings in SQLite, typed everywhere in between.
- **Tags as JSON in a TEXT column.** Pragmatic for SQLite — no junction table needed for a local tool. Search uses `LIKE` over the serialized JSON. If this ever moved to Postgres, it'd become a `text[]` or a real tags table.
- **Indexed the hot paths.** `status`, `priority`, `due_date` — the three columns every filter hits.
- **`plan_day` deduplicates.** Urgent and high-priority queries can overlap with the overdue list, so the final focus list is built with a `seen` set.

---

## Limitations / next steps

- No tests yet — planned: `pytest` with an in-memory SQLite fixture for the repository layer.
- No recurring tasks.
- Search is `LIKE`-based; for a bigger dataset, SQLite FTS5 would be the upgrade.
- Single-user, single-machine by design. Multi-user would mean swapping SQLite for Postgres and adding a user column.

---

## License

MIT
