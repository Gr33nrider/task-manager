from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.middleware import AuthMiddleware
from app.core.database import engine, BaseModel
from app.core.config import settings
from app.core.templates import templates
from app.api.v1.api import api_router
from app.api.v1.routers.pages import pages_router
from app.api.v1.routers.admin import admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    print("\033[32mINFO:\033[0m     Database connection: \033[32mOK\033[0m")
    yield 
    print("\033[32mINFO:\033[0m     Database is disconnected")

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan
    )

BASE_DIR = Path(__file__).parent

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

app.include_router(api_router)
app.include_router(pages_router)
app.include_router(admin_router)
app.add_middleware(AuthMiddleware)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0",port=8000, reload=True)
