from contextlib import asynccontextmanager
from database import engine, BaseModel
import uvicorn
from fastapi import FastAPI
from routers.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    print("INFO:     Database connection: OK")
    yield 
    print("INFO:     Database is disconnected")

app = FastAPI(
    title="Task Planner",
    description="My graduation project",
    version="0.1",
    lifespan=lifespan
    )

app.include_router(users_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1",port=8000, reload=True)
