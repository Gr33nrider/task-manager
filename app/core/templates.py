from fastapi import Request
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.core.config import settings

# Определяем базовую директорию
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Создаём экземпляр шаблонов
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

templates.env.cache={}

templates.env.globals.update({
    "app_name": settings.app_name,
    "app_version": settings.app_version
})

def render_template(request: Request, template_name: str, context: dict = None):
    """Безопасная функция для рендеринга шаблонов"""
    if context is None:
        context = {}
    
    return templates.TemplateResponse(template_name, {"request": request, **context})