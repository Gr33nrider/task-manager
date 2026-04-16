from fastapi import APIRouter, status, HTTPException, Depends
from database import SessionDep
from repository.users import UserRepository
from schemas.user import SUserAdd, SUserResponse, SUserLogin
from schemas.token import SToken
from auth import get_current_user

router = APIRouter(
    prefix="/api/users",
    tags=["Пользователи"]
)


@router.get("")
async def get_all_users(session: SessionDep, offset: int = 0, limit: int = 10) -> list[SUserResponse]:
    users = await UserRepository.get_all(session, offset, limit)
    return users

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: SUserAdd, session: SessionDep) -> SUserResponse:
    
    result = await UserRepository.register(session, user_data)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    return result


@router.post("/login")
async def login(user_data: SUserLogin, session: SessionDep) -> SToken:

    result = await UserRepository.login(session, user_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    return result

@router.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    return current_user

@router.get("/{user_id}")
async def get_user(session: SessionDep, user_id: int) -> SUserResponse:
    
    result = await UserRepository.get_one(session, user_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return result
