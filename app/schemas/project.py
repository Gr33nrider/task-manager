from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class SProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    key: str = Field(..., min_length=1, max_length=10, pattern="^[A-Z0-9]+$")
    description: Optional[str] = None


class SProjectCreate(SProjectBase):
    pass


class SProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None


class SProjectResponse(SProjectBase):
    id: int
    owner_id: int
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)