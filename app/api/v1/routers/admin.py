from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, func, delete, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import SessionDep
from app.core.auth import get_current_admin_user, CurrentUserDep
from app.models.users import UsersModel
from app.models.projects import ProjectsModel
from app.models.tasks import TasksModel
from app.models.user_projects import UserProjectsModel
from app.schemas.user import SUserBase, SUserSettings, SUserUpdate
from app.schemas.project import SProjectUpdate
from app.schemas.task import STaskUpdate
from app.core.templates import templates

admin_router = APIRouter(prefix="/admin", tags=["Админ панель"])


# ==================== Страницы ====================

@admin_router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: CurrentUserDep,
    session: SessionDep
):
    """Главная страница админ-панели"""
    if current_user.role != "admin":
        return RedirectResponse(url="/main", status_code=303)
    
    # Статистика
    users_count = await session.scalar(select(func.count(UsersModel.id)))
    projects_count = await session.scalar(select(func.count(ProjectsModel.id)))
    tasks_count = await session.scalar(select(func.count(TasksModel.id)))
    
    # Последние пользователи
    recent_users_result = await session.execute(
        select(UsersModel).order_by(UsersModel.created_at.desc()).limit(5)
    )
    recent_users = recent_users_result.scalars().all()
    
    # Последние проекты
    recent_projects_result = await session.execute(
        select(ProjectsModel).order_by(ProjectsModel.created_at.desc()).limit(5)
    )
    recent_projects = recent_projects_result.scalars().all()
    

    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {
            "current_user": current_user,
            "users_count": users_count,
            "projects_count": projects_count,
            "tasks_count": tasks_count,
            "recent_users": recent_users,
            "recent_projects": recent_projects,
            "app_name": "Task Manager"
        }
    )


@admin_router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    current_user: CurrentUserDep,
    session: SessionDep,
    page: int = 1,
    search: str = ""
):
    """Управление пользователями"""
    if current_user.role != "admin":
        return RedirectResponse(url="/main", status_code=303)
    
    limit = 20
    offset = (page - 1) * limit
    
    query = select(UsersModel)
    if search:
        query = query.where(
            UsersModel.username.ilike(f"%{search}%") |
            UsersModel.email.ilike(f"%{search}%") |
            UsersModel.full_name.ilike(f"%{search}%")
        )
    
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    result = await session.execute(query.offset(offset).limit(limit).order_by(UsersModel.created_at.desc()))
    users = result.scalars().all()
    
    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {
            "current_user": current_user,
            "users": users,
            "total": total,
            "page": page,
            "total_pages": (total + limit - 1) // limit,
            "search": search,
            "app_name": "Task Manager"
        }
    )


@admin_router.get("/projects", response_class=HTMLResponse)
async def admin_projects(
    request: Request,
    current_user: CurrentUserDep,
    session: SessionDep,
    page: int = 1,
    search: str = ""
):
    """Управление проектами"""
    if current_user.role != "admin":
        return RedirectResponse(url="/main", status_code=303)
    
    limit = 20
    offset = (page - 1) * limit
    
    query = select(ProjectsModel).options(selectinload(ProjectsModel.owner))
    if search:
        query = query.where(ProjectsModel.name.ilike(f"%{search}%") | ProjectsModel.key.ilike(f"%{search}%"))
    
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    result = await session.execute(
        query.offset(offset).limit(limit).order_by(ProjectsModel.created_at.desc())
    )
    projects = result.scalars().all()
    
    return templates.TemplateResponse(
        request,
        "admin/projects.html",
        {
            "current_user": current_user,
            "projects": projects,
            "total": total,
            "page": page,
            "total_pages": (total + limit - 1) // limit,
            "search": search,
            "app_name": "Task Manager"
        }
    )


@admin_router.get("/tasks", response_class=HTMLResponse)
async def admin_tasks(
    request: Request,
    current_user: CurrentUserDep,
    session: SessionDep,
    page: int = 1,
    search: str = ""
):
    """Управление задачами"""
    if current_user.role != "admin":
        return RedirectResponse(url="/main", status_code=303)
    
    limit = 20
    offset = (page - 1) * limit
    
    query = select(TasksModel).options(selectinload(TasksModel.project), selectinload(TasksModel.assignee))
    if search:
        query = query.where(TasksModel.title.ilike(f"%{search}%"))
    
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    result = await session.execute(
        query.offset(offset).limit(limit).order_by(TasksModel.created_at.desc())
    )
    tasks = result.scalars().all()
    
    return templates.TemplateResponse(
        request,
        "admin/tasks.html",
        {
            "current_user": current_user,
            "tasks": tasks,
            "total": total,
            "page": page,
            "total_pages": (total + limit - 1) // limit,
            "search": search,
            "app_name": "Task Manager"
        }
    )


# ==================== CRUD API ====================

# --- Пользователи ---

@admin_router.put("/users/{user_id}")
async def admin_update_user(
    user_id: int,
    user_data: SUserSettings,
    session: SessionDep,
    current_user: CurrentUserDep
):
    """Обновление пользователя админом"""

    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно привилегий для обновления роли пользователя")
    
    if user_data.role == "user" and current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя снять с себя админ роль")
    
    result = await session.execute(select(UsersModel).where(UsersModel.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    await session.commit()
    return {"success": True}


@admin_router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    """Удаление пользователя админом"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно привилегий")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Невозможно удалить себя")
    
    result = await session.execute(select(UsersModel).where(UsersModel.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    await session.delete(user)
    await session.commit()
    return {"success": True}


# --- Проекты ---

@admin_router.put("/projects/{project_id}")
async def admin_update_project(
    project_id: int,
    project_data: SProjectUpdate,
    session: SessionDep,
    current_user: CurrentUserDep
):
    """Обновление проекта админом"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно привилегий")
    
    result = await session.execute(select(ProjectsModel).where(ProjectsModel.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    
    update_data = project_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    
    await session.commit()
    return {"success": True}


@admin_router.delete("/projects/{project_id}")
async def admin_delete_project(
    project_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    """Удаление проекта админом"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно привилегий")
    
    result = await session.execute(select(ProjectsModel).where(ProjectsModel.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    
    # Удаляем связи с пользователями
    await session.execute(delete(UserProjectsModel).where(UserProjectsModel.project_id == project_id))
    
    await session.delete(project)
    await session.commit()
    return {"success": True}


# --- Задачи ---

@admin_router.put("/tasks/{task_id}")
async def admin_update_task(
    task_id: int,
    task_data: STaskUpdate,
    session: SessionDep,
    current_user: CurrentUserDep
):
    """Обновление задачи админом"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await session.execute(select(TasksModel).where(TasksModel.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    await session.commit()
    return {"success": True}


@admin_router.delete("/tasks/{task_id}")
async def admin_delete_task(
    task_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    """Удаление задачи админом"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await session.execute(select(TasksModel).where(TasksModel.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await session.delete(task)
    await session.commit()
    return {"success": True}