from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException, status

from app.core.auth import CurrentUserDep
from app.models.tasks import TasksModel, TaskStatus
from app.schemas.task import STaskCreate, STaskUpdate
from app.api.v1.repository.projects import ProjectRepository
from app.api.v1.repository.users import UserRepository


class TaskRepository:
    
    @classmethod
    async def create_task(
        cls, 
        session: AsyncSession, 
        task_data: STaskCreate,
        current_user: CurrentUserDep,
    ) -> TasksModel:
        """Создать новую задачу"""


        data = task_data.model_dump(exclude_unset=True)

        if "due_date" not in data.keys():
            data["due_date"] = None
        
        if "assignee_id" not in data.keys():
            data["assignee_id"] = None
            
        new_task = TasksModel(**data, author_id = current_user.id)

        new_task.author_id = current_user.id
        
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)


        new_task.project = await ProjectRepository.get_project(task_data.project_id,session,current_user)
        
        return new_task
    


    @classmethod
    async def get_task_by_id(
        cls, 
        session: AsyncSession, 
        task_id: int,
        load_relations: bool = False
    ) -> TasksModel:
        """Получить задачу по ID"""
        query = select(TasksModel).where(TasksModel.id == task_id)
        
        if load_relations:
            query = query.options(
                selectinload(TasksModel.project),
                selectinload(TasksModel.author),
                selectinload(TasksModel.assignee),
                selectinload(TasksModel.subtasks),
                selectinload(TasksModel.comments)
            )
        
        result = await session.execute(query)
        task = result.scalar_one_or_none()

        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        
        return task
    
    @classmethod
    async def get_by_project(
        cls,
        session: AsyncSession,
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        assignee_id: Optional[int] = None
    ) -> List[TasksModel]:
        """Получить задачи проекта с фильтрацией"""
        query = select(TasksModel).where(TasksModel.project_id == project_id).options(selectinload(TasksModel.assignee),selectinload(TasksModel.author))
        
        if status:
            query = query.where(TasksModel.status == status)
        if assignee_id:
            query = query.where(TasksModel.assignee_id == assignee_id)
        
        query = query.offset(skip).limit(limit).order_by(TasksModel.created_at)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def update_task(
        cls,
        session: AsyncSession,
        task_id: int,
        task_update: STaskUpdate,
        current_user_id: int,
        is_admin: bool = False
    ) -> Optional[TasksModel]:
        """Обновить задачу (владелец проекта, админ проекта, автор или админ системы)"""
        task = await cls.get_task_by_id(session, task_id)
        
        if not task:
            return None
        
        project_role = await ProjectRepository.get_project_role(session, task.project_id, current_user_id)
        
        if task.author_id != current_user_id and not is_admin:
            if project_role != "owner" and project_role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно привилегий для обновления задачи"
                )
        
        if not task_update.due_date:
            task_update.due_date = None

        if not task_update.assignee_id:
            task_update.assignee_id = None

        update_data = task_update.model_dump(exclude_unset=True)

        
        for field, value in update_data.items():
            setattr(task, field, value)
        
        await session.commit()
        await session.refresh(task)
        
        return task
    
    @classmethod
    async def delete_task(
        cls,
        session: AsyncSession,
        task_id: int,
        current_user_id: int,
        is_admin: bool = False
    ) -> bool:
        """Удалить задачу"""
        task = await cls.get_task_by_id(session, task_id)
        
        if not task:
            return False
        
        project_role = await ProjectRepository.get_project_role(session, task.project_id, current_user_id)

        if task.author_id != current_user_id and not is_admin:
            if project_role != "owner" and project_role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно привилегий для удаления"
                )
        
        await session.delete(task)
        await session.commit()
        
        return True
    
    @classmethod
    async def update_task_status(
        cls,
        session: AsyncSession,
        task_id: int,
        new_status: TaskStatus,
        current_user_id: int
    ) -> Optional[TasksModel]:
        """Обновить статус задачи (без проверки прав, доступно всем участникам)"""
        task = await cls.get_task_by_id(session, task_id)
        
        if not task:
            return None
        
        if new_status == TaskStatus.DONE and task.status != TaskStatus.DONE:

            task.completed_at = datetime.now()
        
        task.status = new_status
        await session.commit()
        await session.refresh(task)
        
        return task
    
    @classmethod
    async def get_user_tasks(
        cls,
        session: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None
    ) -> List[TasksModel]:
        """Получить задачи, назначенные пользователю"""
        query = select(TasksModel).where(TasksModel.assignee_id == user_id)
        
        if status:
            query = query.where(TasksModel.status == status)
        
        query = query.offset(skip).limit(limit).order_by(TasksModel.due_date, TasksModel.created_at)
        
        result = await session.execute(query)
        return result.scalars().all()
    


