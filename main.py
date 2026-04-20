from contextlib import asynccontextmanager
from app.core.database import engine, BaseModel
import uvicorn
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router


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

app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1",port=8000, reload=True)
