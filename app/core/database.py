from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=10
)

celery_async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    poolclass=NullPool
)

celery_sync_engine = create_engine(
    settings.celery_database_url,
    echo=False,
    pool_size=10,
    max_overflow=20
)


new_session = async_sessionmaker(engine, expire_on_commit=False)

celery_async_new_session = async_sessionmaker(celery_async_engine, expire_on_commit=False
)

celery_sync_new_session = sessionmaker(celery_sync_engine, expire_on_commit=False)

class BaseModel(MappedAsDataclass,DeclarativeBase):
    pass

async def get_db():
    async with new_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]