import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import select, update
from celery import shared_task
from asgiref.sync import async_to_sync

from app.services.gigachat_service import gigachat_service
from app.core.database import celery_async_new_session
from app.models.ai_task import AITasksModel, AITaskStatus
from app.models.subtasks import SubtasksModel
from app.models.tasks import TasksModel

logger = logging.getLogger(__name__)


@shared_task(name="decompose_task", bind=True, acks_late=True)
def decompose_task(self, task_id: int, title: str, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Celery задача для декомпозиции задачи на подзадачи
    """
    try:
        async_to_sync(_update_ai_task_status)(self.request.id, task_id, AITaskStatus.PROCESSING)
        
        subtasks_data = async_to_sync(gigachat_service.decompose_task)(title, description)
        
        created_subtasks = async_to_sync(_save_subtasks)(task_id, subtasks_data)
        
        total_hours = sum(s["estimated_hours"] for s in subtasks_data)
        async_to_sync(_update_task_estimated_time)(task_id, total_hours)
        
        async_to_sync(_update_ai_task_status)(
            self.request.id, 
            task_id, 
            AITaskStatus.COMPLETED,
            output_data={"subtasks": subtasks_data, "total_hours": total_hours}
        )
        
        return {
            "status": "completed",
            "task_id": task_id,
            "subtasks": subtasks_data,
            "total_hours": total_hours
        }
        
    except Exception as e:
        logger.error(f"Decomposition task failed: {e}", exc_info=True)
        async_to_sync(_update_ai_task_status)(
            self.request.id,
            task_id,
            AITaskStatus.FAILED,
            error_message=str(e)
        )
        raise


@shared_task(name="estimate_task_time", bind=True)
def estimate_task_time(self, task_id: int, title: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Оценка времени выполнения задачи"""
    try:
        async_to_sync(_update_ai_task_status)(self.request.id, task_id, AITaskStatus.PROCESSING)
        
        estimated_hours = async_to_sync(gigachat_service.estimate_task_time)(title, description)
        
        async_to_sync(_update_task_estimated_time)(task_id, estimated_hours)
        async_to_sync(_update_ai_task_status)(
            self.request.id,
            task_id,
            AITaskStatus.COMPLETED,
            output_data={"estimated_hours": estimated_hours}
        )
        
        return {
            "status": "completed",
            "task_id": task_id,
            "estimated_hours": estimated_hours
        }
        
    except Exception as e:
        logger.error(f"Estimation task failed: {e}", exc_info=True)
        async_to_sync(_update_ai_task_status)(
            self.request.id,
            task_id,
            AITaskStatus.FAILED,
            error_message=str(e)
        )
        raise

async def _update_ai_task_status(
    celery_task_id: str,
    task_id: int,
    status: AITaskStatus,
    output_data: Optional[Dict] = None,
    error_message: Optional[str] = None
):
    """Обновляет статус AI задачи в БД"""
    async with celery_async_new_session() as session:
       
        stmt = select(AITasksModel).where(AITasksModel.celery_task_id == celery_task_id)
        result = await session.execute(stmt)
        ai_task = result.scalar_one_or_none()
        
        if ai_task is None:
            ai_task = AITasksModel(
                task_id=task_id,
                celery_task_id=celery_task_id,
                status=status,
                task_type="decomposition",
                input_data={}
            )
            session.add(ai_task)
        
        ai_task.status = status
        if output_data:
            ai_task.output_data = output_data
        if error_message:
            ai_task.error_message = error_message
        
        await session.commit()


async def _save_subtasks(task_id: int, subtasks_data: List[Dict]) -> List[Dict]:
    """Сохраняет подзадачи в БД"""
    async with celery_async_new_session() as session:
        created = []
        for idx, sub_data in enumerate(subtasks_data):
            subtask = SubtasksModel(
                task_id=task_id,
                title=sub_data["title"],
                estimated_hours=sub_data["estimated_hours"],
                position=idx,
                is_completed=False
            )
            session.add(subtask)
            created.append({
                "id": subtask.id,
                "title": subtask.title,
                "estimated_hours": subtask.estimated_hours
            })
        
        await session.commit()
        return created


async def _update_task_estimated_time(task_id: int, total_hours: float):
    """Обновляет общее время задачи"""
    async with celery_async_new_session() as session:
        stmt = update(TasksModel).where(TasksModel.id == task_id).values(estimated_hours=total_hours)
        await session.execute(stmt)
        await session.commit()