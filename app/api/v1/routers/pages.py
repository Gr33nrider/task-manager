from functools import wraps
from typing import Callable, Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.core.auth import CurrentUserDep
from app.core.database import SessionDep
from app.core.templates import templates
from app.api.v1.repository.projects import ProjectRepository
from app.api.v1.repository.tasks import TaskRepository
from app.api.v1.repository.users import UserRepository
from app.api.v1.repository.users_projects import UserProjectRepository
from app.models.user_projects import UserProjectsModel
from app.models.users import UsersModel
from app.schemas.task import TaskStatus, STaskCreate
from app.api.v1.repository.ai_tasks import AITasksRepository
from app.api.v1.repository.subtasks import SubtaskRepository


pages_router = APIRouter(include_in_schema=False)


@pages_router.get("/")
async def home(
    request: Request) -> HTMLResponse:
    """Главная страница (редирект на главную или логин)"""
    return RedirectResponse(url="/main" if request.cookies.get("access_token") else "/auth/login")


@pages_router.get("/auth/login")
async def login_page(request: Request, registered: bool = None, logout: bool = None) -> HTMLResponse:
    """Страница входа"""
    
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"registered": (True if registered else False),
         "logout": (True if logout else False)},    
    )


@pages_router.get("/auth/register")
async def register_page(request: Request) -> HTMLResponse:
    """Страница регистрации"""
    return templates.TemplateResponse({"request": request, "current_user": None}, "auth/register.html",)


@pages_router.get("/main")
async def main_page(
    request: Request,
    current_user: CurrentUserDep,
    db: SessionDep
) -> HTMLResponse:
    """Главная страница с профилем и списком проектов"""
    # Получаем проекты пользователя (где он владелец или участник)
    my_projects = await ProjectRepository.get_user_projects(db, current_user)

    # Считаем статистику по задачам
    active_tasks = 0
    total_tasks = 0
    completed_tasks = 0
    
    for project in my_projects:
        tasks = await TaskRepository.get_by_project(db, project.id)
        total_tasks += len(tasks)
        completed_tasks += sum(1 for t in tasks if t.status == TaskStatus.DONE)
    
    active_tasks = total_tasks - completed_tasks
    
    return templates.TemplateResponse(
        request,
        "main/index.html",
        {
            "current_user": current_user,
            "my_projects": my_projects,
            "active_tasks_count": active_tasks,
            "total_tasks_count": total_tasks,
            "completed_tasks_count": completed_tasks,
        }
    )

@pages_router.get("/dashboard/{project_id}")
async def dashboard_page(request: Request, current_user: CurrentUserDep, project_id: int, session: SessionDep)  -> HTMLResponse:
    """Главная доска задач"""

    project = await ProjectRepository.get_project(project_id, session, current_user)

    role = await ProjectRepository.get_project_role(session, project_id, current_user.id)

    owner = False
    admin = False
    member = False
    viewer = False

    if role == "owner":
        owner = True
    if role == "admin":
        admin = True
    if role == member:
        member = True
    if role == "viewer":
        viewer = True
    
    return templates.TemplateResponse( 
        request,
        "dashboard/index.html",
        {
            "project": project,
            "current_user": current_user,
            "owner": owner,
            "admin": admin,
            "member": member,
            "viewer": viewer
        },
        
    )

@pages_router.get("/projects/{project_id}/members", response_class=HTMLResponse)
async def get_project_members(
    request: Request,
    project_id: int,
    current_user: CurrentUserDep,
    session: SessionDep
):
    """HTMX-эндпоинт для получения списка участников проекта"""
    
    # Проверяем доступ к проекту
    project = await ProjectRepository.get_project(project_id,session, current_user)
    
    members = await ProjectRepository.get_members(project_id, request, session, current_user)
    
    # Разделяем по ролям
    project_owner = None
    project_admins = []
    project_members = []
    project_viewers = []
    
    grant_role= ["admin","owner"]
    invite_rights = False
    for member in members:
        if member.role == "owner":
            project_owner = member
        elif member.role == "admin":
            project_admins.append(member)
        elif member.role == "viewer":
            project_viewers.append(member)
        else:
            project_members.append(member)

        if current_user.id == member.user.id and member.role in grant_role:
            invite_rights = True
    
    if current_user.role == 'admin':
        invite_rights = True

    return templates.TemplateResponse(
        request,
        "components/members_list.html",
        {
            "project": project,
            "project_owner": project_owner,
            "project_admins": project_admins,
            "project_members": project_members,
            "project_viewers": project_viewers,
            "current_user": current_user,
            "invite_rights": invite_rights
        }
    )

@pages_router.get("/auth/logout")
async def logout():
    """Выход из системы"""
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token", path="/")
    return response


# User

@pages_router.get("/profile")
async def profile_page(
    request: Request,
    current_user: CurrentUserDep,
    db: SessionDep
) -> HTMLResponse:
    """Страница профиля пользователя"""
    return templates.TemplateResponse(
        request,
        "main/profile.html",
        {
            "current_user": current_user,
        }
    )


# Projects
@pages_router.get("/api/modals/create-project", response_class=HTMLResponse)
async def create_project_modal(
    request: Request
):
    """Модальное окно создания проекта"""
    return templates.TemplateResponse(
        request,
        "projects/modals/create_project.html",
    )

@pages_router.get("/api/projects/check-key")
async def check_project_key(
    key: str,
    session: SessionDep
):
    """Проверка уникальности ключа проекта (для валидации на лету)"""
    from sqlalchemy import select
    from app.models.projects import ProjectsModel
    
    key = key.upper().strip()
    
    if len(key) < 2 or len(key) > 10:
        return {"valid": False, "message": "Ключ должен быть 2-10 символов"}
    
    if not key.isalnum():
        return {"valid": False, "message": "Только буквы и цифры"}
    
    result = await session.execute(
        select(ProjectsModel).where(ProjectsModel.key == key)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return {"valid": False, "message": "Ключ уже используется"}
    
    return {"valid": True, "message": "Ключ доступен"}


@pages_router.get("/project/settings/{project_id}", response_class=HTMLResponse)
async def project_settings_page(
    request: Request,
    project_id: int,
    current_user: CurrentUserDep,
    session: SessionDep
):
    """Страница настроек проекта"""
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    from app.models.projects import ProjectsModel
    from app.models.user_projects import UserProjectsModel, UserProjectRole
    
    # Получаем проект
    result = await session.execute(
        select(ProjectsModel).where(ProjectsModel.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    
    # Проверяем права (только владелец или админ могут управлять настройками)
    if project.owner_id != current_user.id and current_user.role != "admin":
        # Проверяем, является ли пользователь администратором проекта
        member_result = await session.execute(
            select(UserProjectsModel).where(
                UserProjectsModel.project_id == project_id,
                UserProjectsModel.user_id == current_user.id,
                UserProjectsModel.role.in_([UserProjectRole.OWNER, UserProjectRole.ADMIN])
            )
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Отказано в доступе")
    
    # Получаем всех участников проекта
    members_result = await session.execute(
        select(UserProjectsModel)
        .where(UserProjectsModel.project_id == project_id)
        .options(selectinload(UserProjectsModel.user))
    )
    members = members_result.scalars().all()
    
    # Разделяем по ролям
    project_owner = None
    project_admins = []
    project_members = []
    project_viewers = []
    
    for member in members:
        if member.role == UserProjectRole.OWNER:
            project_owner = member
        elif member.role == UserProjectRole.ADMIN:
            project_admins.append(member)
        elif member.role == UserProjectRole.VIEWER:
            project_viewers.append(member)
        else:
            project_members.append(member)
        
    
    # Получаем пользователей, не состоящих в проекте (для приглашения)
    all_users_result = await session.execute(
        select(UsersModel).where(UsersModel.id != current_user.id)
    )
    all_users = all_users_result.scalars().all()
    
    # Исключаем уже добавленных
    member_ids = [m.user_id for m in members]
    available_users = [u for u in all_users if u.id not in member_ids]

    role = await ProjectRepository.get_project_role(session, project_id, current_user.id)

    owner = False
    admin = False
    member = False
    viewer = False

    if role == "owner":
        owner = True
    if role == "admin":
        admin = True
    if role == member:
        member = True
    if role == "viewer":
        viewer = True
    
    return templates.TemplateResponse(
        request,
        "projects/settings.html",
        {
            "project": project,
            "current_user": current_user,
            "project_owner": project_owner,
            "project_admins": project_admins,
            "project_members": project_members,
            "project_viewers": project_viewers,
            "available_users": available_users,
            "owner": owner,
            "admin": admin,
            "member": member,
            "viewer": viewer
        }
    )

@pages_router.get("/modals/{project_id}/invite-member", response_class=HTMLResponse)
async def invite_member_modal(
    request: Request,
    project_id: int,
    current_user: CurrentUserDep,
    session: SessionDep
):
    """
    Модальное окно для приглашения участника в проект
    """
    members = await ProjectRepository.get_members(project_id, request, session, current_user)
    
    project = await ProjectRepository.get_project(project_id, session, current_user)

    existing_member_ids = [member.user_id for member in members]
    
    
    return templates.TemplateResponse(
        request,
        "components/new_member_list.html",
        {
            "project": project,
            "available_users": [],
            "existing_member_ids": existing_member_ids
        }
    )

@pages_router.get("/api/users/search")
async def search_users(
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
    q: str = "", 
):
    """
    API для поиска пользователей по имени или email (для автозаполнения)
    """
    
    if len(q) < 2:
        return JSONResponse(content=[])
    
    # Исключаем текущего пользователя
    query = select(UsersModel).where(
        UsersModel.id != current_user.id,
        UsersModel.is_active == True,
        or_(
            UsersModel.username.ilike(f"%{q}%"),
            UsersModel.email.ilike(f"%{q}%"),
            UsersModel.full_name.ilike(f"%{q}%")
        )
    ).limit(10)
    
    result = await session.execute(query)
    users = result.scalars().all()

    search_list =[
        {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "display": f"{user.full_name or user.username} (@{user.username})"
        }
        for user in users
    ]
    
    return search_list

# Tasks
@pages_router.get("/api/tasks/kanban/{project_id}", response_class=HTMLResponse)
async def get_kanban_board(
    request: Request,
    project_id: int,
    current_user: CurrentUserDep,
    db: SessionDep
):
    """Возвращает HTML Kanban доски для HTMX"""
    
    
    tasks = await TaskRepository.get_by_project(db, project_id)
    
    # Группировка по статусам
    columns = {
        "todo": [],
        "in_progress": [],
        "review": [],
        "done": [],
        "blocked": []
    }
    
    for task in tasks:
        columns[task.status.value].append(task)
    
    return templates.TemplateResponse(
        request,
        "dashboard/kanban_board.html",
        {
            "project_id": project_id,
            "columns": columns,
            "status_labels": {
                "todo": "К выполнению",
                "in_progress": "В работе",
                "review": "На проверке",
                "done": "Готово",
                "blocked": "Заблокировано"
            }
        }
          
    )

@pages_router.get("/api/modals/create-task/{project_id}", response_class=HTMLResponse)
async def create_task_modal(
    project_id: int,
    request: Request,
    current_user: CurrentUserDep, 
    session: SessionDep):
    """Возвращает форму создания задачи"""
    
    project = await ProjectRepository.get_project(project_id, session, current_user)
    all_members = await ProjectRepository.get_members(project_id, request, session, current_user)

    members = []
    for member in all_members:
        if member.role != "viewer":
            members.append(member)



    
    return templates.TemplateResponse(
        request,
        "tasks/modals/task_create.html",
        {
            "project": project,
            "members": members,
            "is_create": True
        }
        
    )

@pages_router.get("/api/modals/task/{task_id}", response_class=HTMLResponse)
async def update_task_modal(
    task_id: int,
    request: Request,
    current_user: CurrentUserDep, 
    session: SessionDep):
    """Возвращает карточку задачи с возможностью обновления"""
    
    task = await TaskRepository.get_task_by_id(session, task_id, load_relations=True)

    all_members = await UserProjectRepository.get_members(task.project_id, session, current_user)

    members = []
    for member in all_members:
        if member.role != "viewer":
            members.append(member)


    role = await ProjectRepository.get_project_role(session, task.project_id, current_user.id)

    owner = False
    admin = False
    member = False
    viewer = False
    author = False

    if role == "owner":
        owner = True
    if role == "admin":
        admin = True
    if role == member:
        member = True
    if role == "viewer":
        viewer = True

    if task.author_id == current_user.id:
        author = True
    
    return templates.TemplateResponse(
        request,
        "tasks/modals/task.html",
        {
            "task": task,
            "members": members,
            "owner": owner,
            "admin": admin,
            "member": member,
            "viewer": viewer,
            "author": author
        }
        
    )


@pages_router.get("/api/modals/task/{task_id}/subtasks", response_class=HTMLResponse)
async def get_subtasks(
    task_id: int,
    request: Request,
    current_user: CurrentUserDep, 
    session: SessionDep):
    """Возвращает карточку задачи с возможностью обновления"""
    
    task = await TaskRepository.get_task_by_id(session, task_id, load_relations=True)

    subtasks = await SubtaskRepository.get_by_task(session, task_id)

    role = await ProjectRepository.get_project_role(session, task.project_id , current_user.id)

    owner = False
    admin = False
    member = False
    viewer = False

    if role == "owner":
        owner = True
    if role == "admin":
        admin = True
    if role == member:
        member = True
    if role == "viewer":
        viewer = True

    if len(subtasks) == 0:
        HTMLResponse(content="""
            <div class="text-center py-3">
                <div class="spinner-border text-primary spinner-border-sm" role="status"></div>
                <p class="mt-2 small">Подзадачи ещё не готовы... Подождите...</p>
            </div>
        """)
    else:
        return templates.TemplateResponse(
            request,
            "components/subtask_list.html",
            {
                "task": task,
                "owner": owner,
                "admin": admin,
                "member": member,
                "viewer": viewer
            }
            
        )


@pages_router.post("/api/tasks/{task_id}/status", response_class=HTMLResponse)
async def update_task_status(
    task_id: int,
    status: str,
    db: SessionDep,
    current_user: CurrentUserDep
):
    """Обновляет статус задачи (drag-and-drop)"""
    
    await TaskRepository.update_task_status(db, task_id, TaskStatus(status), current_user.id)

    return HTMLResponse(content="")


@pages_router.get("/api/tasks/{task_id}/card", response_class=HTMLResponse)
async def get_task_card(
    request: Request,
    task_id: int,
    db: SessionDep,
    current_user: CurrentUserDep
):
    """Возвращает HTML карточки задачи (для обновления после изменений)"""
    
    task = await TaskRepository.get_by_id(db, task_id)
    return templates.TemplateResponse(
        {"request": request, "task": task},
        "components/task_card.html"
    )




@pages_router.get("/api/modals/edit-task/{task_id}", response_class=HTMLResponse)
async def edit_task_modal(
    request: Request, 
    task_id: int,
    db: SessionDep
):
    """Возвращает форму редактирования задачи"""
    
    task = await TaskRepository.get_task_by_id(db, task_id)
    projects = await ProjectRepository.get_all(db)
    users = await UserRepository.get_all(db)
    
    return templates.TemplateResponse(
        {
            "request": request,
            "task": task,
            "projects": projects,
            "users": users,
            "is_create": False
        },
        "dashboard/forms/task_form.html"
    )


@pages_router.post("/api/tasks/create")
async def create_task_form(
    request: Request,
    db: SessionDep,
    current_user: CurrentUserDep
):
    """Создаёт задачу из формы"""
    
    form = await request.form()
    task_data = STaskCreate(
        project_id=int(form.get("project_id")),
        title=form.get("title"),
        description=form.get("description") or None,
        assignee_id=int(form.get("assignee_id")) if form.get("assignee_id") else None
    )
    
    await TaskRepository.create_task(db, task_data, current_user.id)
    
    return RedirectResponse(url=f"/dashboard?project_id={task_data.project_id}", status_code=303)

# AI
@pages_router.post("/api/tasks/{task_id}/ai-decompose", response_class=HTMLResponse)
async def ai_decompose_task(
    request: Request,
    task_id: int,
    db: SessionDep,
    current_user: CurrentUserDep
):
    """Запускает AI-декомпозицию и возвращает список подзадач"""
    
    result = await AITasksRepository.decompose(
        session=db,
        task_id=task_id,
        current_user=current_user
    )
    
    # Подождём немного для демонстрации (в реальности нужен WebSocket или polling)
    import asyncio
    await asyncio.sleep(2)
    
    # Получаем обновлённую задачу с подзадачами
    task = await TaskRepository.get_task_by_id(db, task_id, load_relations=True)
    
    return templates.TemplateResponse(
        "components/subtask_list.html",
        {"request": request, "task": task}
    )


@pages_router.post("/api/subtasks/{subtask_id}/toggle")
async def toggle_subtask(
    subtask_id: int,
    db: SessionDep,
    current_user: CurrentUserDep
):
    """Переключает статус выполнения подзадачи"""
    
    await SubtaskRepository.toggle_complete(db, subtask_id)
    return HTMLResponse(content="")


