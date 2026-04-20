import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.mark.asyncio
async def test_register_user(async_client):
    """Тест регистрации пользователя"""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_login_user(async_client):
    """Тест входа пользователя"""
    # Регистрируем пользователя
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "testpassword123"
        }
    )
    assert register_response.status_code == 201
    
    # Логинимся
    login_response = await async_client.post(
        "/api/v1/auth/login",
        data={
            "username": "loginuser",
            "password": "testpassword123"
        }
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_user(async_client):
    """Тест регистрации существующего пользователя"""
    # Первая регистрация
    first_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "duplicateuser",
            "password": "testpassword123"
        }
    )
    assert first_response.status_code == 201
    
    # Попытка зарегистрировать того же пользователя
    second_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "duplicateuser",
            "password": "testpassword123"
        }
    )
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "User with this email or username already exists"