from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from app.api.v1.repository.users import UserRepository
from app.core.database import SessionDep
from app.core.auth import OAuth2Dep
from app.schemas.user import SUserAdd, SUserResponse
from app.schemas.token import SToken

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: Request, session: SessionDep) -> SUserResponse:
    """Регистрация пользователя"""
    try:
        result = await UserRepository.register(session, request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

@router.post("/login")
async def login(
    response: Response,
    session: SessionDep, 
    form_data: OAuth2Dep
) -> SToken:
    """Авторизация пользователя (генерация access_token)"""

    result = await UserRepository.login(response, session, form_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )
    
    return result
    

    
    