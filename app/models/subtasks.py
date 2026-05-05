from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import BaseModel

from app.models.tasks import TasksModel


class SubtasksModel(BaseModel):
    __tablename__ = "subtasks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, init=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), init=False)
    
    # Relationships
    task: Mapped["TasksModel"] = relationship("TasksModel", back_populates="subtasks", init=False)
    