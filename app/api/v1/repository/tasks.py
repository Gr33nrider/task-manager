from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime

from app.models.tasks import TasksModel, TaskStatus
from app.schemas.task import STaskCreate, STaskUpdate


class TaskRepository:
    
    @classmethod
    async def create_task(
        cls, 
        session: AsyncSession, 
        task_data: STaskCreate, 
        author_id: int
    ) -> TasksModel:
        """Создать новую задачу"""
        
        data = task_data.model_dump()

        new_task = TasksModel(**data, author_id=author_id)

        new_task.author_id = author_id
        
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)
        
        return new_task
    


    @classmethod
    async def get_task_by_id(
        cls, 
        session: AsyncSession, 
        task_id: int,
        load_relations: bool = False
    ) -> Optional[TasksModel]:
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
        return result.scalar_one_or_none()
    
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
        query = select(TasksModel).where(TasksModel.project_id == project_id)
        
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
        """Обновить задачу (только автор или админ)"""
        task = await cls.get_task_by_id(session, task_id)
        
        if not task:
            return None
        
        
        if task.author_id != current_user_id and not is_admin:
            raise PermissionError("Not enough permissions to update this task")
        
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
        
        if task.author_id != current_user_id and not is_admin:
            raise PermissionError("Not enough permissions to delete this task")
        
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
    


