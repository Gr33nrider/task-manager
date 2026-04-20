from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, ForeignKey, Text, Date, Enum as SQLEnum
from sqlalchemy.sql import func
from typing import Optional, TYPE_CHECKING
from app.core.database import BaseModel
from datetime import datetime, date
import enum


if TYPE_CHECKING:
    from app.models.projects import ProjectsModel
    from app.models.users import UsersModel


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"



class TasksModel(BaseModel):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, init=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    parent_task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    story_points: Mapped[Optional[int]] = mapped_column(nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


    # project 1 <--> M tasks
    project: Mapped["ProjectsModel"] = relationship(
        "ProjectsModel", back_populates="tasks"
    )
    # user 1 <--> M tasks
    author: Mapped["UsersModel"] = relationship(
        "UsersModel", foreign_keys=[author_id], back_populates="created_tasks"
    )
    # user 1 <--> M tasks
    assignee: Mapped[Optional["UsersModel"]] = relationship(
        "UsersModel", foreign_keys=[assignee_id], back_populates="assigned_tasks"
    )
    # parent_task 1 <--> M tasks
    parent_task: Mapped[Optional["TasksModel"]] = relationship("TasksModel", remote_side=[id], backref="subtasks")

    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.TODO)
    priority: Mapped[TaskPriority] = mapped_column(SQLEnum(TaskPriority), default=TaskPriority.LOW)