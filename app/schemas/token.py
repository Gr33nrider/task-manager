from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    

class STokenData(BaseModel):
    sub: Optional[str] = None
    exp: Optional[datetime] = None