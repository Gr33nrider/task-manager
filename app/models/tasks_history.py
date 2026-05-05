from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.core.database import BaseModel

if TYPE_CHECKING:
    from app.models.users import UsersModel
    from app.models.tasks import TasksModel


class TaskHistoryAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    STATUS_CHANGE = "status_change"
    ASSIGN = "assign"


class TasksHistoryModel(BaseModel):
    __tablename__ = "task_history"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(SQLEnum(TaskHistoryAction), nullable=False)
    field_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    # Relationships
    task: Mapped["TasksModel"] = relationship("TasksModel", back_populates="history")
    user: Mapped["UsersModel"] = relationship("UsersModel", back_populates="history_entries")
