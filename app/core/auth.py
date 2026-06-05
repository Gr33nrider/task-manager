from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Request, status, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.users import UsersModel
from app.core.database import SessionDep
from app.schemas.token import STokenData


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    
    return encoded_jwt


async def get_token_from_request(request: Request, token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """
    Извлекает токен из разных источников в порядке приоритета:
    1. Cookie 'access_token' (HttpOnly)
    2. Заголовок Authorization: Bearer <token>
    3. Параметр запроса 'token' (опционально)
    """
    # 1. Проверяем cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
    
    # 2. Проверяем заголовок Authorization
    if token:
        return token
    
    # 3. Проверяем параметр запроса (для WebSocket или тестирования)
    query_token = request.query_params.get("token")
    if query_token:
        return query_token
    
    return None


async def get_current_user(
        request: Request,
        session: SessionDep, 
        token: Optional[str] = Depends(get_token_from_request)
    ) -> UsersModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        token_data = STokenData(sub=user_id)
        
    except JWTError:
        raise credentials_exception
    
    result = await session.execute(
        select(UsersModel).where(UsersModel.id == int(token_data.sub))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: UsersModel = Depends(get_current_user),
) -> UsersModel:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: UsersModel = Depends(get_current_user),
) -> UsersModel:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


OAuth2Dep = Annotated[OAuth2PasswordRequestForm, Depends()]
CurrentUserDep = Annotated[UsersModel, Depends(get_current_active_user)]