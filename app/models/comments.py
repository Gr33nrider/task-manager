from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import BaseModel


if TYPE_CHECKING:
    from app.models.users import UsersModel
    from app.models.tasks import TasksModel


class CommentsModel(BaseModel):
    __tablename__ = "comments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mentions: Mapped[List[int]] = mapped_column(JSON, default=list)
    attachments: Mapped[List[dict]] = mapped_column(JSON, default=list)
    is_edited: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), init=False)
    updated_at: Mapped[datetime] = mapped_column(onupdate=func.now(), server_default=func.now(), init=False)
    
    
    task: Mapped["TasksModel"] = relationship("TasksModel", back_populates="comments", init=False)
    author: Mapped["UsersModel"] = relationship("UsersModel", back_populates="comments", init=False)
    parent_comment: Mapped[Optional["CommentsModel"]] = relationship("CommentsModel", remote_side=[id], backref="replies", init=False)
    