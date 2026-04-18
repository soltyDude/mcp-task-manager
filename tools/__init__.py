from datetime import date
from typing import Optional

from mcp.server.fastmcp import Context

from core import Task, TaskCreate, TaskStatus, TaskUpdate, TaskSummary, TaskRepository


def _repo(ctx: Context) -> TaskRepository:
    return ctx.request_context.lifespan_context["repo"]


async def create_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: Optional[str] = None,
    tags: Optional[str] = None,
    ctx: Context = None,
) -> Task:
    """Create a new task.

    Args:
        title: Task title (required)
        description: Detailed description
        priority: low | medium | high | urgent
        due_date: YYYY-MM-DD format
        tags: Comma-separated tags, e.g. "work,backend"
    """
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    data = TaskCreate(title=title, description=description, priority=priority,
                      due_date=due_date, tags=tag_list)
    return _repo(ctx).create(data)


async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    ctx: Context = None,
) -> list[Task]:
    """List tasks with optional filters.

    Args:
        status: pending | in_progress | completed | cancelled
        priority: low | medium | high | urgent
    """
    return _repo(ctx).list_all(status=status, priority=priority)


async def get_task(task_id: int, ctx: Context = None) -> Task:
    """Get a task by ID.

    Args:
        task_id: Task ID
    """
    task = _repo(ctx).get_by_id(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    return task


async def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    due_date: Optional[str] = None,
    tags: Optional[str] = None,
    ctx: Context = None,
) -> Task:
    """Update an existing task.

    Args:
        task_id: Task ID to update
        title: New title
        description: New description
        priority: low | medium | high | urgent
        status: pending | in_progress | completed | cancelled
        due_date: YYYY-MM-DD format
        tags: Comma-separated tags
    """
    tag_list = [t.strip() for t in tags.split(",")] if tags is not None else None
    data = TaskUpdate(title=title, description=description, priority=priority,
                      status=status, due_date=due_date, tags=tag_list)
    task = _repo(ctx).update(task_id, data)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    return task


async def delete_task(task_id: int, ctx: Context = None) -> str:
    """Delete a task by ID.

    Args:
        task_id: Task ID to delete
    """
    task = _repo(ctx).get_by_id(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    _repo(ctx).delete(task_id)
    return f"Task '{task.title}' (ID: {task_id}) deleted."


async def complete_task(task_id: int, ctx: Context = None) -> Task:
    """Mark a task as completed.

    Args:
        task_id: Task ID to complete
    """
    task = _repo(ctx).update(task_id, TaskUpdate(status=TaskStatus.COMPLETED))
    if not task:
        raise ValueError(f"Task {task_id} not found")
    return task


async def search_tasks(query: str, ctx: Context = None) -> list[Task]:
    """Search tasks by keyword across title, description, and tags.

    Args:
        query: Search keyword or phrase
    """
    return _repo(ctx).search(query)


async def get_summary(ctx: Context = None) -> TaskSummary:
    """Get task statistics: counts by status and priority, overdue count."""
    return _repo(ctx).summary()


async def plan_day(ctx: Context = None) -> str:
    """Build a prioritized focus list for today.

    Returns urgent + high priority non-completed tasks, plus overdue ones.
    Useful for starting a work session with Claude.
    """
    repo = _repo(ctx)
    today = date.today().isoformat()

    urgent = repo.list_all(status="pending", priority="urgent") + \
             repo.list_all(status="in_progress", priority="urgent")
    high = repo.list_all(status="pending", priority="high") + \
           repo.list_all(status="in_progress", priority="high")

    # deduplicate (urgent already included in high query if filters overlap)
    seen = set()
    focus = []
    for t in urgent + high:
        if t.id not in seen:
            seen.add(t.id)
            focus.append(t)

    overdue = [
        t for t in repo.list_all()
        if t.due_date and t.due_date.date().isoformat() < today
        and t.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)
        and t.id not in seen
    ]

    lines = [f"📅 Day plan for {today}", ""]

    if overdue:
        lines.append("⚠️  OVERDUE")
        for t in overdue:
            lines.append(f"  [{t.id}] {t.title}  (due {t.due_date.date()})")
        lines.append("")

    if focus:
        lines.append("🔥 FOCUS (urgent + high priority)")
        for t in focus:
            tag_str = f"  #{' #'.join(t.tags)}" if t.tags else ""
            lines.append(f"  [{t.id}] [{t.priority.value.upper()}] {t.title}{tag_str}")
    else:
        lines.append("✅ No urgent/high tasks — looks clear!")

    summary = repo.summary()
    lines += [
        "",
        f"📊 Total: {summary.total_tasks} | "
        f"In progress: {summary.in_progress_tasks} | "
        f"Overdue: {summary.overdue_tasks}",
    ]

    return "\n".join(lines)
