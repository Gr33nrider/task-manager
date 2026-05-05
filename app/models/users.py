from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from typing import Optional, List, TYPE_CHECKING
from app.core.database import BaseModel
from datetime import datetime
import enum

if TYPE_CHECKING:
    from app.models.projects import ProjectsModel
    from app.models.tasks import TasksModel
    from app.models.user_projects import UserProjectsModel
    from app.models.comments import CommentsModel
    from app.models.tasks_history import TasksHistoryModel
    from app.models.ai_suggestions import AISuggestionsModel

class UserRole(str, enum.Enum):
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"

class UsersModel(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, init=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER, init=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, init=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), init=False)
    
    # user 1 <--> M projects 
    owned_projects: Mapped[List["ProjectsModel"]] = relationship(
        "ProjectsModel", back_populates="owner", cascade="all, delete-orphan", init=False
        )
    
    # user 1 <--> M created tasks
    created_tasks: Mapped[List["TasksModel"]] = relationship(
        "TasksModel", foreign_keys="TasksModel.author_id", back_populates="author", init=False
    )

    # user 1 <--> M assignee tasks
    assigned_tasks: Mapped[List["TasksModel"]] = relationship(
        "TasksModel", foreign_keys="TasksModel.assignee_id", back_populates="assignee", init=False
    )

    #
    projects: Mapped[List["UserProjectsModel"]] = relationship(
        "UserProjectsModel", back_populates="user", cascade="all, delete-orphan", init=False
    )

    comments: Mapped[List["CommentsModel"]] = relationship(
        "CommentsModel", back_populates="author", cascade="all, delete-orphan", init=False
    )
    history_entries: Mapped[List["TasksHistoryModel"]] = relationship(
        "TasksHistoryModel", back_populates="user", cascade="all, delete-orphan", init=False
    )
    ai_suggestions: Mapped[List["AISuggestionsModel"]] = relationship(
        "AISuggestionsModel", back_populates="user", cascade="all, delete-orphan", init=False
    )