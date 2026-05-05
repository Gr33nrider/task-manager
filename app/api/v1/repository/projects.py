from fastapi import Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import UsersModel
from app.models.projects import ProjectsModel
from app.core.auth import get_current_active_user
from app.schemas.project import SProjectCreate, SProjectUpdate

class ProjectRepository:

    @classmethod
    async def get_all(
        cls, 
        session: AsyncSession, 
        current_user: UsersModel = Depends(get_current_active_user), 
        offset: int = 0, 
        limit: int = 10
    ):
        
        if current_user.role != "admin":
            raise PermissionError

        query = select(ProjectsModel).offset(offset).limit(limit)

        result = await session.execute(query)

        projects = result.scalars().all()

        return projects
    
    @classmethod
    async def list_projects(
        cls, 
        session: AsyncSession, 
        current_user: UsersModel = Depends(get_current_active_user), 
        offset: int = 0, 
        limit: int = 10
    ):

        query = select(ProjectsModel).where(ProjectsModel.owner_id == current_user.id).offset(offset).limit(limit)

        projects = await session.execute(query)

        return projects.scalars().all()
    
    @classmethod
    async def create_project(
        cls, 
        session: AsyncSession,
        project_data: SProjectCreate, 
        current_user: UsersModel = Depends(get_current_active_user)
    ):
        

        query = select(ProjectsModel).where(ProjectsModel.key == project_data.key)

        result = await session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project with this key already exists"
            )
        
        project = ProjectsModel(
            **project_data.model_dump(),
            owner_id=current_user.id
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        
        return project
    

    @classmethod
    async def get_project(
        cls,
        project_id: int,
        session: AsyncSession,
        current_user: UsersModel = Depends(get_current_active_user)
    ):
        
        query = select(ProjectsModel).where(ProjectsModel.id == project_id) 

        result = await session.execute(query)

        project = result.scalar_one_or_none()
    
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        
        if project.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        return project
    


    @classmethod
    async def update_project(
        cls,
        project_id: int,
        project_update: SProjectUpdate,
        session: AsyncSession,
        current_user: UsersModel = Depends(get_current_active_user)
    ):
        
        query = select(ProjectsModel).where(ProjectsModel.id == project_id)

        result = await session.execute(query)
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        
        if project.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        
        update_data = project_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)
        
        await session.commit()
        await session.refresh(project)
        
        return project
    

    @classmethod
    async def delete_project(
        cls,
        project_id: int,
        session: AsyncSession,
        current_user: UsersModel = Depends(get_current_active_user)
    ):
        
        query = select(ProjectsModel).where(ProjectsModel.id == project_id)

        result = await session.execute(query)
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if project.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        await session.delete(project)
        await session.commit()
