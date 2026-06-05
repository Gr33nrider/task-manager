from fastapi import Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import UsersModel
from app.models.projects import ProjectsModel
from app.models.user_projects import UserProjectsModel, UserProjectRole
from app.core.auth import get_current_active_user
from app.schemas.project import SProjectCreate, SProjectUpdate

class UserProjectRepository:

    @classmethod
    async def get_members(
        cls,
        project_id: int,
        session: AsyncSession,
        current_user: UsersModel = Depends(get_current_active_user),
    ):
        
        query = select(UserProjectsModel).where(UserProjectsModel.project_id == project_id).options(selectinload(UserProjectsModel.user))

        result = await session.execute(query)

        members = result.scalars().all()
        return members

