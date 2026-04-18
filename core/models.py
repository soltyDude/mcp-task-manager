from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=1000)
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat() if v else None}}


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str = ""
    priority: Priority = Priority.MEDIUM
    due_date: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[str] = None
    tags: Optional[list[str]] = None


class TaskSummary(BaseModel):
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    cancelled_tasks: int
    urgent_tasks: int
    overdue_tasks: int
