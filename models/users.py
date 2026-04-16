from sqlalchemy.orm import Mapped, mapped_column
from database import BaseModel
from datetime import datetime

class UsersModel(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    email: Mapped[str]
    username: Mapped[str]
    hashed_password: Mapped[str]
    full_name: Mapped[str]
    role: Mapped[str] = mapped_column(default="user")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())