# tests/conftest.py
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from main import app
from app.core.config import settings
from app.core.database import BaseModel, get_db

test_engine = create_async_engine(settings.test_database_url, echo=False)

async def test_get_db():
    """Тестовая зависимость для БД"""
    async with async_sessionmaker(test_engine, expire_on_commit=False)() as session:
        yield session


app.dependency_overrides[get_db] = test_get_db

@pytest_asyncio.fixture(scope="function")
async def async_client():
    """Создаёт новый клиент с чистой БД для каждого теста"""
    
    # Создаём все таблицы заново
    async with test_engine.begin() as conn:
        # Очищаем и создаём схему
        await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)
    
    # Создаём транспорт с приложением
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # Закрываем соединение после теста
    await test_engine.dispose()