from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from models import HTMLRender
from pydantic import BaseModel

class Item(BaseModel):
    name: str = "skipupdate"
    age: int = 0

app = FastAPI(title="Task Planner")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class = HTMLResponse)
async def home_render_HTML(request: Request):
    html = HTMLRender(request)
    return html.render("index.html", page = "Home")

@app.get("/registration", response_class = HTMLResponse) 
async def registration_render_HTML(request: Request):
    html = HTMLRender(request)
    return html.render("register.html", page = "Registration")

@app.get("/login", response_class = HTMLResponse) 
async def login_render_HTML(request: Request):
    html = HTMLRender(request)
    return html.render("login.html", page = "Login")

fake_db = [{"user_id": 1, "name": "sasha", "age": 20}, 
           {"user_id": 2, "name": "anton", "age": 25}, 
           {"user_id": 3, "name": "grisha", "age": 21}, 
           {"user_id": 4 ,"name": "vitaliy", "age": 21}, 
           {"user_id": 5,"name": "vova", "age": 19}]


# Создать пользователя
@app.post("/api/v1/users")
async def create_user(item: Item):
    counter = len(fake_db) + 1
    fake_db.append({"user_id": counter, "name": item.name, "age": item.age})
    return {"Status": "Пользователь создан!"},fake_db

# Получить всех пользователей
@app.get("/api/v1/users")
async def get_all_users(skip: int = 0, limit: int = 2):
    return fake_db[skip : skip + limit]

     
# Получить одного пользователя
@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: int):
    return [user for user in fake_db if user["user_id"] == user_id]

# Обновить информацию пользователя
@app.patch("/api/v1/users/{user_id}")
async def update_user(user_id: int, item: Item):
    updatable_user = [user for user in fake_db if user["user_id"] == user_id]
    if item.name != "skipupdate": updatable_user[0]["name"] = item.name
    if item.age != 0: updatable_user[0]["age"] = item.age
    return updatable_user[0]

# Удалить пользователя
@app.delete("/api/v1/users/{user_id}")
async def delete_user(user_id: int):
    fake_db.pop(user_id - 1)
    return {"Status": "Пользователь удален!"}, fake_db



    


