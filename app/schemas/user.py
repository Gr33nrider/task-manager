from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.users import UserRole
from typing import Optional
from datetime import datetime

class SUserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=5, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    role: UserRole = UserRole.USER


class SUserAdd(SUserBase):
    password: str = Field(..., min_length=8, max_length=100)

class SUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)

class SUserResponse(SUserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SUserSettings(BaseModel):
    is_active: Optional[bool] = None
    role: UserRole = UserRole.USER

class SUserLogin(BaseModel):
    username: str
    password: str
