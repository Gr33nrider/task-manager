from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select

from app.core.database import SessionDep
from app.core.auth import CurrentUserDep
from app.models.users import UsersModel
from app.models.ai_task import AITasksModel
from app.schemas.ai_task import (
    DecomposeRequest, DecomposeResponse, 
    AITaskStatusResponse, SubtaskResponse
)
from app.api.v1.repository.ai_tasks import AITasksRepository

router = APIRouter(prefix="/ai", tags=["Декомпозиция задач"])


@router.post("/decompose", status_code=status.HTTP_202_ACCEPTED)
async def start_decomposition(
    request: DecomposeRequest,
    session: SessionDep,
    current_user: CurrentUserDep
) -> DecomposeResponse:
    """
    Запускает AI-декомпозицию задачи.
    Возвращает ID задачи в очереди немедленно.
    """
    try:
        result = await AITasksRepository.decompose(
            request=request,
            session=session,
            current_user=current_user
        )

        return result

    except Exception as e:
        raise e


@router.get("/status/{ai_task_id}")
async def get_ai_task_status(
    ai_task_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
) -> AITaskStatusResponse:
    """Проверяет статус AI задачи"""
    
    try:
        result = await AITasksRepository.get_status(ai_task_id, session, current_user)
        return result
    except HTTPException:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI task not found"
            )



@router.get("/task/{task_id}/subtasks")
async def get_task_subtasks(
    task_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
) -> list[SubtaskResponse]:
    """Получает все подзадачи для задачи (результат декомпозиции)"""

    try:
        
        result = await AITasksRepository.get_all(task_id, session)
        return result

    except Exception as e:
        print(e)
    
