from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.database import SessionDep
from app.core.auth import CurrentUserDep
from app.models.users import UsersModel
from app.models.tasks import TasksModel
from app.models.ai_task import AITasksModel, AITaskStatus
from app.models.subtasks import SubtasksModel
from app.schemas.ai_task import (
    DecomposeRequest, DecomposeResponse, 
    AITaskStatusResponse, SubtaskResponse
)

from app.celery.ai_tasks import decompose_task

class AITasksRepository:

    @classmethod
    async def decompose(
        cls,
        request: DecomposeRequest,
        session: SessionDep,
        current_user: CurrentUserDep
    ) -> DecomposeResponse:
        query = select(TasksModel).where(TasksModel.id == request.task_id)
        result = await session.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
    
        if task.author_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        ai_task = AITasksModel(
        task_id=request.task_id,
        status=AITaskStatus.PENDING,
        task_type="decomposition",
        input_data={"title": task.title, "description": task.description}
        )

        session.add(ai_task)
        await session.commit()
        await session.refresh(ai_task)

        celery_result = decompose_task.delay(
            task_id=request.task_id,
            title=task.title,
            description=task.description
        )

        ai_task.celery_task_id = celery_result.id
        await session.commit()

        return DecomposeResponse(
            ai_task_id=ai_task.id,
            task_id=request.task_id,
            status=ai_task.status,
            celery_task_id=celery_result.id,
            message="Task decomposition started. Use /ai/status/{ai_task_id} to check progress."
        )
    
    @classmethod
    async def get_status(
        cls,
        ai_task_id: int,
        db: SessionDep,
        current_user: CurrentUserDep
    ) -> AITaskStatusResponse:
        
        query = select(AITasksModel).where(AITasksModel.id == ai_task_id)
        result = await db.execute(query)
        ai_task = result.scalar_one_or_none()

        if not ai_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI task not found"
            )
        
        return ai_task


    
    @classmethod
    async def get_all(
        cls,
        task_id: int,
        session: SessionDep
    ) -> list[SubtaskResponse]:
        query = select(SubtasksModel).where(SubtasksModel.task_id == task_id).order_by(SubtasksModel.position)
        result = await session.execute(query)
        subtasks = result.scalars().all()

        return subtasks


