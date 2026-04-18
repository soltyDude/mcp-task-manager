import json
import sqlite3
from datetime import datetime
from typing import Optional

from core.models import Priority, Task, TaskCreate, TaskStatus, TaskSummary, TaskUpdate


class TaskRepository:
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    title       TEXT    NOT NULL,
                    description TEXT    DEFAULT '',
                    priority    TEXT    DEFAULT 'medium',
                    status      TEXT    DEFAULT 'pending',
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    due_date    TIMESTAMP NULL,
                    tags        TEXT    DEFAULT '[]'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status   ON tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON tasks(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_due_date ON tasks(due_date)")

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            priority=Priority(row["priority"]),
            status=TaskStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
            due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
            tags=json.loads(row["tags"]) if row["tags"] else [],
        )

    def create(self, data: TaskCreate) -> Task:
        due_date = None
        if data.due_date:
            due_date = datetime.fromisoformat(data.due_date).isoformat()

        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO tasks (title, description, priority, due_date, tags) VALUES (?, ?, ?, ?, ?)",
                (data.title, data.description, data.priority.value, due_date, json.dumps(data.tags)),
            )
            task_id = cursor.lastrowid
            conn.commit()
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            return self._row_to_task(row)

    def get_by_id(self, task_id: int) -> Optional[Task]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            return self._row_to_task(row) if row else None

    def list_all(self, status: Optional[str] = None, priority: Optional[str] = None) -> list[Task]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        query += " ORDER BY created_at DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_task(r) for r in rows]

    def search(self, query: str) -> list[Task]:
        """Full-text search across title, description, and tags."""
        pattern = f"%{query.lower()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM tasks
                   WHERE lower(title) LIKE ?
                      OR lower(description) LIKE ?
                      OR lower(tags) LIKE ?
                   ORDER BY created_at DESC""",
                (pattern, pattern, pattern),
            ).fetchall()
            return [self._row_to_task(r) for r in rows]

    def update(self, task_id: int, data: TaskUpdate) -> Optional[Task]:
        if not self.get_by_id(task_id):
            return None

        fields, params = [], []

        if data.title is not None:
            fields.append("title = ?"); params.append(data.title)
        if data.description is not None:
            fields.append("description = ?"); params.append(data.description)
        if data.priority is not None:
            fields.append("priority = ?"); params.append(data.priority.value)
        if data.status is not None:
            fields.append("status = ?"); params.append(data.status.value)
        if data.due_date is not None:
            due = datetime.fromisoformat(data.due_date).isoformat() if data.due_date else None
            fields.append("due_date = ?"); params.append(due)
        if data.tags is not None:
            fields.append("tags = ?"); params.append(json.dumps(data.tags))

        if not fields:
            return self.get_by_id(task_id)

        fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(task_id)

        with self._connect() as conn:
            conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params)

        return self.get_by_id(task_id)

    def delete(self, task_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0

    def summary(self) -> TaskSummary:
        with self._connect() as conn:
            def count(where: str) -> int:
                return conn.execute(f"SELECT COUNT(*) FROM tasks WHERE {where}").fetchone()[0]

            return TaskSummary(
                total_tasks=count("1=1"),
                pending_tasks=count("status = 'pending'"),
                in_progress_tasks=count("status = 'in_progress'"),
                completed_tasks=count("status = 'completed'"),
                cancelled_tasks=count("status = 'cancelled'"),
                urgent_tasks=count("priority = 'urgent'"),
                overdue_tasks=count("due_date < datetime('now') AND status != 'completed'"),
            )
