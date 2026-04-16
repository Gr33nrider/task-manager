from pydantic import BaseModel
from typing import Optional

class SToken(BaseModel):
    access_token: str
    token_type: str

class STokenData(BaseModel):
    username: Optional[str] = None