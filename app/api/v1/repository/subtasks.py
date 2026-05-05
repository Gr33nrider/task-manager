from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.models.subtasks import SubtasksModel
from app.models.tasks import TasksModel
from app.schemas.task import SSubtaskCreate, SSubtaskUpdate


class SubtaskRepository:
    
    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        task_id: int,
        subtask_data: SSubtaskCreate
    ) -> SubtasksModel:
        """Создать подзадачу"""
        new_subtask = SubtasksModel(
            task_id=task_id,
            title=subtask_data.title,
            estimated_hours=subtask_data.estimated_hours,
            is_completed=subtask_data.is_completed
        )
        
        session.add(new_subtask)
        await session.commit()
        await session.refresh(new_subtask)
        
        return new_subtask
    
    @classmethod
    async def get_by_task(
        cls,
        session: AsyncSession,
        task_id: int
    ) -> List[SubtasksModel]:
        """Получить все подзадачи задачи"""
        result = await session.execute(
            select(SubtasksModel)
            .where(SubtasksModel.task_id == task_id)
            .order_by(SubtasksModel.position)
        )
        return result.scalars().all()
    
    @classmethod
    async def update(
        cls,
        session: AsyncSession,
        subtask_id: int,
        subtask_update: SSubtaskUpdate
    ) -> Optional[SubtasksModel]:
        """Обновить подзадачу"""
        result = await session.execute(
            select(SubtasksModel).where(SubtasksModel.id == subtask_id)
        )
        subtask = result.scalar_one_or_none()
        
        if not subtask:
            return None
        
        update_data = subtask_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subtask, field, value)
        
        await session.commit()
        await session.refresh(subtask)
        
        return subtask
    
    @classmethod
    async def delete(
        cls,
        session: AsyncSession,
        subtask_id: int
    ) -> bool:
        """Удалить подзадачу"""
        result = await session.execute(
            select(SubtasksModel).where(SubtasksModel.id == subtask_id)
        )
        subtask = result.scalar_one_or_none()
        
        if not subtask:
            return False
        
        await session.delete(subtask)
        await session.commit()
        
        return True