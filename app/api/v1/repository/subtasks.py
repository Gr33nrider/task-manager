from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, update
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

        query = select(func.max(SubtasksModel.position)).where(SubtasksModel.task_id == task_id)

        max_pos_result = await session.execute(query)
        max_position = max_pos_result.scalar() or 0
        
        new_subtask = SubtasksModel(
            task_id=task_id,
            title=subtask_data.title,
            estimated_hours=subtask_data.estimated_hours,
            position=max_position + 1,
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
    
    @classmethod
    async def toggle_complete(
        cls,
        session: AsyncSession,
        subtask_id: int
    ) -> Optional[SubtasksModel]:
        """Переключить статус выполнения подзадачи"""
        # Получаем подзадачу
        result = await session.execute(
            select(SubtasksModel).where(SubtasksModel.id == subtask_id)
        )
        subtask = result.scalar_one_or_none()
        
        if not subtask:
            return None
        
        # Переключаем статус
        subtask.is_completed = not subtask.is_completed
        await session.commit()
        await session.refresh(subtask)
        
        # Обновляем общее время задачи
        # Получаем все подзадачи задачи
        subtasks_result = await session.execute(
            select(SubtasksModel).where(SubtasksModel.task_id == subtask.task_id)
        )
        all_subtasks = subtasks_result.scalars().all()
        
        # Вычисляем общее время только для НЕвыполненных подзадач (опционально)
        # или оставляем общее время как сумму всех подзадач
        total_hours = sum(s.estimated_hours or 0 for s in all_subtasks)
        
        # Обновляем задачу
        await session.execute(
            update(TasksModel)
            .where(TasksModel.id == subtask.task_id)
            .values(estimated_hours=total_hours)
        )
        await session.commit()
        
        return subtask