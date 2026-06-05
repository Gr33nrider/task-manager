from datetime import datetime
from sqlalchemy import ForeignKey, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum
from typing import TYPE_CHECKING
from app.core.database import BaseModel

if TYPE_CHECKING:
    from app.models.users import UsersModel
    from app.models.projects import ProjectsModel


class UserProjectRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class UserProjectsModel(BaseModel):
    __tablename__ = "user_projects"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now(), init=False)
    
    # user 1 <--> M project member
    user: Mapped["UsersModel"] = relationship("UsersModel", back_populates="projects")

    # project 1 <--> M user members
    project: Mapped["ProjectsModel"] = relationship("ProjectsModel", back_populates="members")

    role: Mapped[str] = mapped_column(SQLEnum(UserProjectRole), default=UserProjectRole.MEMBER)

    