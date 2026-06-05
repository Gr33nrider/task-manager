from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import SessionDep
from app.core.auth import CurrentUserDep, get_current_active_user
from app.schemas.project import SProjectCreate, SProjectUpdate, SProjectResponse
from app.models.users import UsersModel
from app.models.projects import ProjectsModel
from app.api.v1.repository.projects import ProjectRepository

router = APIRouter(
    prefix="/projects", 
    tags=["Проекты"])


@router.get("")
async def get_all_projects(
    session: SessionDep,
    current_user: UsersModel = Depends(get_current_active_user) ,
    offset: int = 0,
    limit: int = 10
) -> List[SProjectResponse]:
    """Получить список всех проектов (только админ)"""
    try:
        projects = await ProjectRepository.get_all(session, current_user, offset, limit)
        return projects
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        ) 
    

@router.get("/my")
async def get_my_projects(
    session: SessionDep,
    current_user: UsersModel = Depends(get_current_active_user) ,
    offset: int = 0,
    limit: int = 10
) -> List[SProjectResponse]:
    """Получить список созданных проектов текущего пользователя"""

    projects = await ProjectRepository.list_projects(session, current_user, offset, limit)
    return projects
    


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: SProjectCreate,
    session: SessionDep,
    current_user: UsersModel = Depends(get_current_active_user)
) -> SProjectResponse:
    """Создать новый проект"""

    project = await ProjectRepository.create_project(session, project_data, current_user)

    return project
        


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    session: SessionDep,
    current_user: UsersModel = Depends(get_current_active_user)
) -> SProjectResponse:
    """Получить проект по ID"""

    project = await ProjectRepository.get_project(project_id, session, current_user)

    return project


@router.put("/{project_id}")
async def update_project(
    project_id: int,
    project_update: SProjectUpdate,
    session: SessionDep,
    current_user: UsersModel = Depends(get_current_active_user)
) -> SProjectResponse:
    """Обновить проект (только владелец или админ)"""

    project = await ProjectRepository.update_project(project_id, project_update, session, current_user)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    session: SessionDep,
    current_user: UsersModel = Depends(get_current_active_user)
):
    """Удалить проект (только владелец или админ)"""
    
    await ProjectRepository.delete_project(project_id, session, current_user)

@router.post("/{project_id}/add-member")
async def add_project_member(
    project_id: int,
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep
):
    result = await ProjectRepository.add_member(project_id, request, session, current_user)

    if result:
        return {"msg": "Added"}


@router.delete("/{project_id}/remove-member/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: int,
    user_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    result = await ProjectRepository.remove_member(project_id, user_id, session, current_user)



@router.put("/{project_id}/update-member-role")
async def update_member_role(
    project_id: int,
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep
):
    result = await ProjectRepository.update_member(project_id,request,session,current_user)

