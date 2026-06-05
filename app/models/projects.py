from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING, List
from app.core.database import BaseModel
from datetime import datetime
import enum

if TYPE_CHECKING:
    from app.models.users import UsersModel
    from app.models.tasks import TasksModel
    from app.models.user_projects import UserProjectsModel

class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"



class ProjectsModel(BaseModel):
    __tablename__ = "projects"
    
    id: Mapped[int] =  mapped_column(primary_key=True, init=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(SQLEnum(ProjectStatus), default=ProjectStatus.ACTIVE, init=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), init=False)
    
    # projects M <--> 1 user 
    owner: Mapped["UsersModel"] = relationship(
        "UsersModel", back_populates="owned_projects"
    )
    
    # projects 1 <--> M tasks
    tasks: Mapped[List["TasksModel"]] = relationship(
        "TasksModel", back_populates="project", cascade="all, delete-orphan" , init=False
    )

    #
    members: Mapped[List["UserProjectsModel"]] = relationship(
        "UserProjectsModel", back_populates="project", cascade="all, delete-orphan", init=False
    )

    
