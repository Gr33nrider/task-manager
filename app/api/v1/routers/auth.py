from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.repository.users import UserRepository
from app.core.database import SessionDep
from app.core.auth import OAuth2Dep
from app.schemas.user import SUserAdd, SUserResponse
from app.schemas.token import SToken

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: SUserAdd, session: SessionDep) -> SUserResponse:
    """Регистрация пользователя"""
    try:
        result = await UserRepository.register(session, user_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

@router.post("/login")
async def login(session: SessionDep, form_data: OAuth2Dep) -> SToken:
    """Авторизация пользователя (генерация access_token)"""

    result = await UserRepository.login(session, form_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    return result
    
    