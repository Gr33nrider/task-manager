from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from auth import get_password_hash, verify_password, create_access_token 
from models.users import UsersModel
from schemas.user import SUserAdd, SUserLogin
from schemas.token import SToken
from dotenv import load_dotenv
import os
from datetime import timedelta
load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

class UserRepository:


    @classmethod
    async def register(cls, session: AsyncSession, data: SUserAdd) -> UsersModel | None:
        
        query = select(UsersModel).where((UsersModel.username == data.username) | (UsersModel.email == data.email))

        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if user is not None:
            return None
        
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
    async def login(cls, session: AsyncSession, user_data: SUserLogin) -> SToken | None:

        query = select(UsersModel).where(UsersModel.username == user_data.username)

        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(user_data.password, user.hashed_password):
            return None
        
            # Создаем JWT токен
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, 
            expires_delta=access_token_expires
        )
        
        return SToken(access_token=access_token, token_type="bearer")
    

    @classmethod
    async def get_all(cls, session: AsyncSession, offset: int, limit: int):
        query = select(UsersModel).offset(offset).limit(limit)

        users = await session.execute(query)

        return users.scalars().all()
    

    @classmethod
    async def get_one(cls, session: AsyncSession, user_id: int):
        query = select(UsersModel).where(UsersModel.id == user_id)

        user = await session.execute(query)

        return user.scalar_one_or_none()
