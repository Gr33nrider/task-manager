from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_password_hash, verify_password, create_access_token, OAuth2Dep, get_current_active_user 
from app.models.users import UsersModel
from app.schemas.user import SUserAdd, SUserLogin, SUserUpdate
from app.schemas.token import SToken
from app.core.config import settings
from datetime import timedelta


ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes

class UserRepository:


    @classmethod
    async def register(cls, session: AsyncSession, data: SUserAdd) -> UsersModel | None:
        
        query = select(UsersModel).where((UsersModel.username == data.username) | (UsersModel.email == data.email))

        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if user is not None:
            raise ValueError("User with this email or username already exists")
        
        hashed_password = get_password_hash(data.password)
        new_user = UsersModel(
            username=data.username, 
            email=data.email, 
            hashed_password=hashed_password, 
            full_name=data.full_name)
        
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
    
        return new_user
    
    @classmethod
    async def login(cls, session: AsyncSession, form_data: OAuth2Dep) -> SToken | None:

        query = select(UsersModel).where(UsersModel.username == form_data.username)

        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            return None
        
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires
        )
        
        return SToken(access_token=access_token)
    

    @classmethod
    async def get_all(cls, session: AsyncSession, current_user: UsersModel = Depends(get_current_active_user), offset: int = 0, limit: int = 10):
        
        if current_user.role != "admin":
            raise PermissionError

        query = select(UsersModel).offset(offset).limit(limit)

        users = await session.execute(query)

        return users.scalars().all()
    

    @classmethod
    async def get_one(cls, session: AsyncSession, user_id: int):
        query = select(UsersModel).where(UsersModel.id == user_id)

        user = await session.execute(query)

        return user.scalar_one_or_none()
    
    @classmethod
    async def update(cls, session: AsyncSession, user_id: int, user_update: SUserUpdate, current_user: UsersModel = Depends(get_current_active_user)):
        if current_user.id != user_id and current_user.role != "admin":
            raise PermissionError
        
        query = select(UsersModel).where(UsersModel.id == user_id)

        result = await session.execute(query)

        user = result.scalar_one_or_none()

        if not user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            update_data["password"] = get_password_hash(update_data.pop("password"))

        for key, value in update_data.items():
            setattr(user, key, value)

        await session.commit()
        await session.refresh(user)

        return user
