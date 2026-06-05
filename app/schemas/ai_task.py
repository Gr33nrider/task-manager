# app/schemas/ai_task.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class AITaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DecomposeRequest(BaseModel):
    task_id: int


class DecomposeResponse(DecomposeRequest):
    ai_task_id: int
    status: AITaskStatus
    celery_task_id: str
    message: str = "Task decomposition started"


class AITaskStatusResponse(BaseModel):
    id: int
    task_id: Optional[int]
    celery_task_id: Optional[str]
    status: AITaskStatus
    task_type: str
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class SubtaskResponse(BaseModel):
    id: int
    title: str
    estimated_hours: float
    is_completed: bool