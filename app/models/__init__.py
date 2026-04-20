
from app.core.database import BaseModel

# Сначала импортируем модели без внешних ключей
from app.models.users import UsersModel, UserRole

# Потом модели, которые зависят от User
from app.models.projects import ProjectsModel
from app.models.user_projects import UserProjectsModel

# Затем модели, которые зависят от Project
from app.models.tasks import TasksModel, TaskStatus, TaskPriority


__all__ = [
    "BaseModel",
    "UsersModel",
    "UserRole",
    "ProjectsModel",
    "UserProjectsModel",
    "TasksModel",
    "TaskStatus",
    "TaskPriority"
]