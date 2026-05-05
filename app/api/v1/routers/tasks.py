from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select
from typing import Optional, List

from app.core.database import SessionDep
from app.core.auth import CurrentUserDep
from app.api.v1.repository.tasks import TaskRepository
from app.api.v1.repository.subtasks import SubtaskRepository
from app.schemas.task import (
    STaskCreate, STaskUpdate, STaskResponse,
    SSubtaskCreate, SSubtaskUpdate, SSubtaskResponse,
    TaskStatus
)

from app.models.projects import ProjectsModel

router = APIRouter(prefix="/tasks", tags=["Задачи"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: STaskCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> STaskResponse:
    """
    Создать новую задачу
    """

    result = await session.execute(
        select(ProjectsModel).where(ProjectsModel.id == task_data.project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create task in this project"
        )
    
    task = await TaskRepository.create_task(session, task_data, current_user.id)
    return task


@router.get("/{task_id}")
async def get_task(
    task_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
) -> STaskResponse:
    """
    Получить задачу по ID
    """
    task = await TaskRepository.get_task_by_id(session, task_id, load_relations=True)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.put("/{task_id}")
async def update_task(
    task_id: int,
    task_update: STaskUpdate,
    session: SessionDep,
    current_user: CurrentUserDep
) -> STaskResponse:
    """
    Обновить задачу (только автор или админ)
    """
    try:
        task = await TaskRepository.update_task(
            session, 
            task_id, 
            task_update, 
            current_user.id,
            current_user.role == "admin"
        )
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return task
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this task"
        )


@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: int,
    new_status: TaskStatus,
    session: SessionDep,
    current_user: CurrentUserDep
) -> STaskResponse:
    """
    Обновить статус задачи (доступно всем участникам проекта)
    """
    task = await TaskRepository.update_task_status(session, task_id, new_status, current_user.id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    """
    Удалить задачу (только автор или админ)
    """
    try:
        deleted = await TaskRepository.delete_task(
            session, 
            task_id, 
            current_user.id,
            current_user.role == "admin"
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this task"
        )



@router.get("/project/{project_id}")
async def get_project_tasks(
    project_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    status: Optional[TaskStatus] = None,
    assignee_id: Optional[int] = None
) -> List[STaskResponse]:
    """
    Получить все задачи проекта с фильтрацией
    """
    tasks = await TaskRepository.get_by_project(
        session, project_id, skip, limit, status, assignee_id
    )
    return tasks


@router.get("/user/me")
async def get_my_tasks(
    session: SessionDep,
    current_user: CurrentUserDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    status: Optional[TaskStatus] = None
) -> List[STaskResponse]:
    """
    Получить задачи, назначенные текущему пользователю
    """
    tasks = await TaskRepository.get_user_tasks(
        session, current_user.id, skip, limit, status
    )
    return tasks


@router.get("/{task_id}/subtasks")
async def get_task_subtasks(
    task_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
) -> List[SSubtaskResponse]:
    """
    Получить все подзадачи задачи
    """
    task = await TaskRepository.get_task_by_id(session, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    subtasks = await SubtaskRepository.get_by_task(session, task_id)
    return subtasks


@router.post("/{task_id}/subtasks", status_code=status.HTTP_201_CREATED)
async def create_subtask(
    task_id: int,
    subtask_data: SSubtaskCreate,
    session: SessionDep,
    current_user: CurrentUserDep
) -> SSubtaskResponse:
    """
    Добавить подзадачу к задаче
    """
    task = await TaskRepository.get_task_by_id(session, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    subtask = await SubtaskRepository.create(session, task_id, subtask_data)
    return subtask


@router.put("/subtasks/{subtask_id}")
async def update_subtask(
    subtask_id: int,
    subtask_update: SSubtaskUpdate,
    session: SessionDep,
    current_user: CurrentUserDep
) -> SSubtaskResponse:
    """
    Обновить подзадачу
    """
    subtask = await SubtaskRepository.update(session, subtask_id, subtask_update)
    
    if not subtask:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subtask not found"
        )
    
    return subtask


@router.delete("/subtasks/{subtask_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subtask(
    subtask_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    """
    Удалить подзадачу
    """
    deleted = await SubtaskRepository.delete(session, subtask_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subtask not found"
        )