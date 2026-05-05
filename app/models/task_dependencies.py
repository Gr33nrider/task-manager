from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.core.database import BaseModel

if TYPE_CHECKING:
    from app.models.tasks import TasksModel



class DependencyType(str, enum.Enum):
    BLOCKS = "blocks"
    RELATES_TO = "relates_to"
    DUPLICATES = "duplicates"

class TaskDependenciesModel(BaseModel):
    __tablename__ = "task_dependencies"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    depends_on_task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    dependency_type: Mapped[str] = mapped_column(SQLEnum(DependencyType), default=DependencyType.BLOCKS)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), init=False)
    
    # Relationships
    task: Mapped["TasksModel"] = relationship("TasksModel", foreign_keys=[task_id], back_populates="dependencies", init=False)
    depends_on: Mapped["TasksModel"] = relationship("TasksModel", foreign_keys=[depends_on_task_id], init=False)
