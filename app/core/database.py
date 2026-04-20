from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from app.core.config import settings


engine = create_async_engine(settings.database_url)

new_session = async_sessionmaker(engine, expire_on_commit=False)

class BaseModel(MappedAsDataclass,DeclarativeBase):
    pass

async def get_db():
    async with new_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]