from typing import List

from fastapi import Depends, HTTPException, Request, status

from sqlalchemy import delete, select, update, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import UsersModel
from app.models.projects import ProjectsModel
from app.models.user_projects import UserProjectsModel, UserProjectRole
from app.core.auth import CurrentUserDep, get_current_active_user
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
        """Получить все проекты"""
        if current_user.role != "admin":
            return None

        query = select(ProjectsModel).offset(offset).limit(limit)

        result = await session.execute(query)

        projects = result.scalars().all()

        return projects
    
    @classmethod
    async def list_projects(
        cls, 
        session: AsyncSession, 
        current_user: UsersModel = Depends(get_current_active_user), 
    ):
        """ Получить проекты за авторством пользователя"""
        query = select(ProjectsModel).where(ProjectsModel.owner_id == current_user.id
                                            ).options(selectinload(ProjectsModel.tasks))

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
                detail="Проект с таким ключом уже существует"
            )
        
        data = project_data.model_dump()

        project = ProjectsModel(
            **data,
            owner_id=current_user.id,
            owner= current_user
        )

        
        session.add(project)

        userproject = UserProjectsModel(user_id=current_user.id, project_id=project.id, role=UserProjectRole.OWNER, user=current_user, project=project)

        session.add(userproject)
        await session.commit()
        await session.refresh(project)


        return project
    
    @classmethod
    async def get_user_projects(
        cls,
        session: AsyncSession,
        current_user: UsersModel,
        offset: int = 0,
        limit: int = 100
    ) -> List[ProjectsModel]:
        """
        Получить все проекты, к которым пользователь имеет доступ:
        - Проекты, где он владелец
        - Проекты, где он участник (через user_projects)
        """
        # Получаем ID проектов, где пользователь участник
        member_project_ids = await session.execute(
            select(UserProjectsModel.project_id).where(
                UserProjectsModel.user_id == current_user.id
            )
        )
        member_ids = [row[0] for row in member_project_ids.all()]
        
        # Получаем проекты (владелец или участник)
        query = select(ProjectsModel).where(
            or_(
                ProjectsModel.owner_id == current_user.id,
                ProjectsModel.id.in_(member_ids)
            )
        ).options(selectinload(ProjectsModel.tasks))
        
        result = await session.execute(query)
        projects = result.scalars().all()
        
        # Добавляем роль пользователя в каждом проекте
        for project in projects:
            if project.owner_id == current_user.id:
                project.user_role = "owner"
            else:
                role_result = await session.execute(
                    select(UserProjectsModel.role).where(
                        UserProjectsModel.project_id == project.id,
                        UserProjectsModel.user_id == current_user.id
                    )
                )
                role = role_result.scalar_one_or_none()
                project.user_role = role or "member"
        
        return projects

    @classmethod
    async def get_project(
        cls,
        project_id: int,
        session: AsyncSession,
        current_user: UsersModel
    ):

        query = select(ProjectsModel).where(ProjectsModel.id == project_id)
        result = await session.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Проект не найден"
            )
        
        has_access = await cls.check_access(project_id, session, current_user)
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет разрешений для просмотра этого проекта"
            )
        
        await session.refresh(project, attribute_names=["owner"])
        
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
                detail="Проект не найден"
            )
        
        project_role = await cls.get_project_role(session, project_id, current_user.id)
        
        if (project.owner_id != current_user.id and current_user.role != "admin"):
            if project_role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно привилегий"
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

    @classmethod
    async def add_member(
        cls,
        project_id: int,
        request: Request,
        session: AsyncSession,
        current_user: CurrentUserDep
    ):
        """Добавление участника в проект"""
        form = await request.form()
        user_id = int(form.get("user_id"))
        role = form.get("role")
        
        # Проверяем права (только владелец или админ)
        project = await session.execute(
            select(ProjectsModel).where(ProjectsModel.id == project_id)
        )
        project = project.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")
        
        project_role = await cls.get_project_role(session, project_id, current_user.id)
        
        if project.owner_id != current_user.id and current_user.role != "admin":
            if project_role != "admin":
                raise HTTPException(status_code=403, detail="Недостаточно привилегий")
        
        # Проверяем, не состоит ли уже пользователь в проекте
        existing = await session.execute(
            select(UserProjectsModel).where(
                UserProjectsModel.project_id == project_id,
                UserProjectsModel.user_id == user_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь уже в проекте")
        
        query = select(UsersModel).where(UsersModel.id == user_id)
        result = await session.execute(query)

        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь не найден")

        # Добавляем участника
        member = UserProjectsModel(
            user_id=user_id,
            project_id=project_id,
            user=user,
            project=project,
            role=UserProjectRole(role)
        )
        session.add(member)
        await session.commit()

        return member
    
    @classmethod
    async def remove_member(
        cls,
        project_id: int,
        user_id: int,
        session: AsyncSession,
        current_user: CurrentUserDep
    ):
        """Удаление участника из проекта"""
        # Проверяем права
        project = await session.execute(
            select(ProjectsModel).where(ProjectsModel.id == project_id)
        )
        project = project.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")
        
        if project.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Недостаточно привилегий")
        
        # Нельзя удалить владельца
        if project.owner_id == user_id:
            raise HTTPException(status_code=400, detail="Нельзя удалить владельца")
        
        query = delete(UserProjectsModel).where(
                UserProjectsModel.project_id == project_id,
                UserProjectsModel.user_id == user_id
            )
        # Удаляем участника
        await session.execute(query)
        await session.commit()
    
    @classmethod
    async def update_member(
    cls,
    project_id: int,
    request: Request,
    session: AsyncSession,
    current_user: CurrentUserDep
    ):
        """Обновление роли участника"""
        data = await request.json()
        user_id = data.get("user_id")
        role = data.get("role")
        
        # Проверяем права
        project = await session.execute(
            select(ProjectsModel).where(ProjectsModel.id == project_id)
        )
        project = project.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")
        
        project_role = await cls.get_project_role(session, project_id, current_user.id)
               
        if project.owner_id != current_user.id and current_user.role != "admin":
            if project_role != "admin":
                raise HTTPException(status_code=403, detail="Недостаточно привилегий")
        
        # Нельзя изменять роль владельца
        if project.owner_id == user_id:
            raise HTTPException(status_code=400, detail="Нельзя изменить роль создателя")
        
        
        query = update(UserProjectsModel).where(
                UserProjectsModel.project_id == project_id,
                UserProjectsModel.user_id == int(user_id)
            ).values(role=UserProjectRole(role)) 

        await session.execute(query)
        await session.commit()
        
        return {"success": True}
    

    @classmethod
    async def get_members(
        cls,
        project_id: int,
        request: Request,
        session: AsyncSession,
        current_user: CurrentUserDep
    ):
        
        has_access = await cls.check_access(project_id, session, current_user)
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно привилегий для этого проекта"
            )

        query = select(UserProjectsModel).where(UserProjectsModel.project_id == project_id).options(selectinload(UserProjectsModel.user)) 

        result = await session.execute(query)
        members = result.scalars().all()

        if len(members) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="В проекте нет участников"
            )

        return members
    
    @classmethod
    async def check_access(
        cls,
        project_id: int,
        session: AsyncSession,
        current_user: CurrentUserDep
    ):
        # Проверяем права
        project = await session.execute(
            select(ProjectsModel).where(ProjectsModel.id == project_id)
        )
        project = project.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")
        
        has_access = False

        # 1. Владелец проекта
        if project.owner_id == current_user.id:
            has_access = True
        
        # 2. Администратор системы
        elif current_user.role == "admin":
            has_access = True
        
        # 3. Участник проекта
        else:
            member_query = select(UserProjectsModel).where(
                UserProjectsModel.project_id == project_id,
                UserProjectsModel.user_id == current_user.id
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()
            if member:
                has_access = True
        
        return has_access
    
    @classmethod
    async def get_project_role(
        cls,
        session: AsyncSession,
        project_id: int,
        user_id: int,
    ):
        
        query = select(UserProjectsModel).where(UserProjectsModel.project_id == project_id, UserProjectsModel.user_id == user_id)

        result = await session.execute(query)

        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(status_code=404, detail="Пользователь не участвует в проекте") 
        
        return member.role
        

