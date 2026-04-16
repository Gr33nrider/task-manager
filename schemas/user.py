from pydantic import BaseModel


class SUserBase(BaseModel):
    email: str
    username: str
    full_name: str


class SUserAdd(BaseModel):
    email: str
    username: str
    full_name: str
    password: str

class SUserResponse(SUserBase):
    id: int
    email: str
    username: str
    full_name: str

class SUserLogin(BaseModel):
    username: str
    password: str
