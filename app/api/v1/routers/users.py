from fastapi import APIRouter, Request, status, HTTPException, Depends

from app.core.database import SessionDep
from app.core.auth import get_current_user, get_current_active_user, CurrentUserDep, get_password_hash, verify_password
from app.api.v1.repository.users import UserRepository
from app.schemas.user import SUserResponse, SUserUpdate
from app.models.users import UsersModel

router = APIRouter(
    prefix="/users",
    tags=["Пользователи"]
)

@router.get("/me")
async def get_current_user(current_user: CurrentUserDep) -> SUserResponse:
    """Получить информацию о текущем пользователе"""

    return current_user

@router.get("")
async def get_all_users(
    session: SessionDep, 
    current_user: UsersModel = Depends(get_current_active_user) ,
    offset: int = 0, 
    limit: int = 10
) -> list[SUserResponse]:
    """Получить всех пользователей (только админ)"""

    try:
        users = await UserRepository.get_all(session, current_user, offset, limit)
        return users
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )




@router.get("/{user_id}")
async def get_user_by_id(session: SessionDep, user_id: int) -> SUserResponse:
    """Получить пользователя по ID """

    result = await UserRepository.get_one(session, user_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return result

@router.put("/{user_id}")
async def update_user(session: SessionDep, 
    user_id: int, 
    request: Request, 
    current_user: CurrentUserDep 
) -> SUserResponse:
    """Обновить информацию о пользователе"""
    
    try:

        user = await UserRepository.update(session, user_id, request, current_user)
        if not user:
           raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return  user
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    """
    Удаление пользователя по ID (П)
    """
    await UserRepository.delete(user_id,session,current_user)

