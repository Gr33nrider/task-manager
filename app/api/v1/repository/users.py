from fastapi import Depends, Request, Response, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import CurrentUserDep, get_password_hash, verify_password, create_access_token, OAuth2Dep, get_current_active_user 
from app.models.users import UsersModel
from app.schemas.user import SUserAdd, SUserLogin, SUserUpdate
from app.schemas.token import SToken
from app.core.config import settings
from datetime import timedelta


ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes

class UserRepository:


    @classmethod
    async def register(cls, session: AsyncSession, request: Request) -> UsersModel | None:
        
        form = await request.form()

        new_user_data = {}

        new_user_data["username"] = form.get("username")
        if len(new_user_data["username"]) < 8:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Имя пользователя должно включать не менее 8 символов")
        elif len(new_user_data["username"]) > 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Имя пользователя слишком большое")

        if form.get("full_name"):
            new_user_data["full_name"] = form.get("full_name")

        new_user_data["email"] = form.get("email")
        
        new_user_data["password"] = form.get("password")
        if len(new_user_data["password"]) < 8:
           raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пароль должен включать не менее 8 символов")
        elif len(new_user_data["password"]) > 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пароль слишком большой")
        
        new_user_data["role"] = "user"

        data = SUserAdd(**new_user_data)

        query = select(UsersModel).where((UsersModel.username == data.username) | (UsersModel.email == data.email))

        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if user is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким именем или почтой уже существует")
        
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
    async def login(cls, response: Response ,session: AsyncSession, form_data: OAuth2Dep) -> SToken | None:

        query = select(UsersModel).where((UsersModel.username == form_data.username) | (UsersModel.email == form_data.username))

        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            return None
        
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,      
            secure=False,      
            samesite="lax",
            max_age=1800,
            path="/"
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
    async def update(cls, session: AsyncSession, user_id: int, request: Request, current_user: UsersModel = Depends(get_current_active_user)):
        if current_user.id != user_id and current_user.role != "admin":
            raise PermissionError
        

        form = await request.form()

        update_data = {}
        if form.get("username"):
            update_data["username"] = form.get("username")
        if form.get("full_name"):
            update_data["full_name"] = form.get("full_name")
        if form.get("email"):
            update_data["email"] = form.get("email")

        if form.get("new_password"):

            if not verify_password(form.get("current_password"), current_user.hashed_password):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Текущий пароль введен неверно")
            
            if len(form.get("new_password")) < 8:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пароль должен содержать не менее 8 символов")
            
            if form.get("new_password") == form.get("new_password2") :
                update_data["password"] = form.get("new_password")
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пароли не совпадают")

                
        
        user_update = SUserUpdate(**update_data)

        query = select(UsersModel).where(UsersModel.id == user_id)

        result = await session.execute(query)

        user = result.scalar_one_or_none()

        if not user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data["password"])

        for key, value in update_data.items():
            setattr(user, key, value)

        await session.commit()
        await session.refresh(user)

        return user
    
    @classmethod
    async def delete(
        cls,
        user_id: int,
        session: AsyncSession,
        current_user: CurrentUserDep
    ):
        if current_user.id != user_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет привелегий для удаления"
            )

        query = select(UsersModel).where(UsersModel.id == user_id)

        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        if user.role == "admin":

            query = select(UsersModel).where(UsersModel.role == "admin")

            admin_count = await session.execute(query)

            if len(admin_count.scalars().all()) == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Нельзя удалить последнего администратора"
                )
        
        await session.delete(user)
        await session.commit()
