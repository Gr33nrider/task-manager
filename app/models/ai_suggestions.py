from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.core.database import BaseModel

if TYPE_CHECKING:
    from app.models.users import UsersModel
    from app.models.tasks import TasksModel

class AISuggestionType(str, enum.Enum):
    DECOMPOSITION = "decomposition"
    ESTIMATION = "estimation"
    RESCHEDULE = "reshedule"


class AISuggestionsModel(BaseModel):
    __tablename__ = "ai_suggestions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    suggestion_type: Mapped[str] = mapped_column(SQLEnum(AISuggestionType), nullable=False)
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    output_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_accepted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    acceptance_feedback: Mapped[Optional[str]] = mapped_column(nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    # Relationships
    task: Mapped[Optional["TasksModel"]] = relationship("TasksModel", back_populates="ai_suggestions")
    user: Mapped["UsersModel"] = relationship("UsersModel", back_populates="ai_suggestions")
    
