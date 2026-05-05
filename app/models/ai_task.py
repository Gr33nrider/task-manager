from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
import enum
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.database import BaseModel


class AITaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AITasksModel(BaseModel):
    __tablename__ = "ai_tasks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, init=False)
    task_id: Mapped[Optional[int]] = mapped_column(nullable=True)  
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, init=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[AITaskStatus] = mapped_column(SQLEnum(AITaskStatus), default=AITaskStatus.PENDING)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, init=False)
    error_message: Mapped[Optional[str]] = mapped_column(nullable=True, init=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), init=False)
    updated_at: Mapped[datetime] = mapped_column(onupdate=func.now(), server_default=func.now(), init=False)