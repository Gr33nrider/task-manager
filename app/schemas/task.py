from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from app.models.tasks import TaskStatus, TaskPriority


class STaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.LOW
    estimated_hours: Optional[float] = Field(None, ge=0, le=1000)
    story_points: Optional[int] = Field(None, ge=0, le=100)
    due_date: Optional[date] = None


class STaskCreate(STaskBase):
    project_id: int
    assignee_id: Optional[int] = None
    parent_task_id: Optional[int] = None


class STaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    estimated_hours: Optional[float] = Field(None, ge=0, le=1000)
    story_points: Optional[int] = Field(None, ge=0, le=100)
    due_date: Optional[date] = None

class STaskResponse(STaskBase):
    id: int
    project_id: int
    author_id: int
    assignee_id: Optional[int]
    parent_task_id: Optional[int]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SSubtaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    estimated_hours: Optional[float] = Field(None, ge=0, le=100)
    is_completed: bool = False


class SSubtaskCreate(SSubtaskBase):
    task_id: int


class SSubtaskResponse(SSubtaskBase):
    id: int
    task_id: int
    position: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)