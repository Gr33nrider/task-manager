from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import SessionDep
from app.core.auth import get_current_active_user
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
    


@router.post("/", status_code=status.HTTP_201_CREATED)
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