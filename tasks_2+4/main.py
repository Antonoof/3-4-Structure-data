from fastapi import (
    FastAPI,
    Request,
    Form,
    HTTPException,
    Depends,
    Cookie,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from passlib.context import CryptContext
from typing import Literal
import json
import time
import base64
import hmac
import hashlib
import random
from faker import Faker
from datetime import datetime, timedelta
import jwt


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
USERS_FILE = "users.json"
SECRET_KEY = "mysecret"
ALGORITHM = "HS256"


class UserRegister(BaseModel):
    name: str
    group: str
    login: str
    password: str
    role: Literal["student", "teacher", "admin"]


class UserLogin(BaseModel):
    login: str
    password: str


def read_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def write_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def encode_jwt(payload):
    header = (
        base64.urlsafe_b64encode(
            json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
        )
        .decode()
        .rstrip("=")
    )
    payload_encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode())
        .decode()
        .rstrip("=")
    )
    signature = hmac.new(
        SECRET_KEY.encode(),
        f"{header}.{payload_encoded}".encode(),
        hashlib.sha256,
    ).digest()
    signature_encoded = (
        base64.urlsafe_b64encode(signature).decode().rstrip("=")
    )
    return f"{header}.{payload_encoded}.{signature_encoded}"


def decode_jwt(token):
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signature_check = hmac.new(
            SECRET_KEY.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256,
        ).digest()
        if (
            base64.urlsafe_b64encode(signature_check).decode().rstrip("=")
            != signature_b64
        ):
            return None
        return json.loads(
            base64.urlsafe_b64decode(payload_b64 + "===").decode()
        )
    except Exception:
        return None


def get_current_user(token: str = Cookie(None)):
    payload = decode_jwt(token)
    if not payload or payload["exp"] < time.time():
        raise HTTPException(401, "Invalid or expired token")
    return payload


def require_role(*roles):
    def checker(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(403, "Access denied")
        return user

    return checker


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": None}
    )


@app.post("/login", response_class=HTMLResponse)
def login_user(
    request: Request, login: str = Form(...), password: str = Form(...)
):
    users = read_users()
    user = next((u for u in users if u["login"] == login), None)
    if not user or not pwd_context.verify(password, user["hashed_password"]):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Неверные данные"}
        )

    token = jwt.encode(
        {
            "sub": user["login"],
            "role": user.get("role"),
            "name": user["name"],
            "group": user.get("group"),
            "exp": datetime.utcnow() + timedelta(hours=1),
        },
        SECRET_KEY,  # type: ignore
        algorithm=ALGORITHM,
    )

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="token", value=token, httponly=True)
    return response


@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse(
        "register.html", {"request": request, "error": None}
    )


@app.post("/register", response_class=HTMLResponse)
def register_user(
    request: Request,
    name: str = Form(...),
    group: str = Form(...),
    login: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
):
    users = read_users()
    if any(u["login"] == login for u in users):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Логин уже существует"},
        )

    users.append(
        {
            "name": name,
            "group": group,
            "login": login,
            "role": role,
            "hashed_password": pwd_context.hash(password),
        }
    )
    write_users(users)
    return RedirectResponse(
        url="/login", status_code=status.HTTP_303_SEE_OTHER
    )


@app.post("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("token")
    return response


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    def __init__(self):
        self.head = None

    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        last = self.head
        while last.next:
            last = last.next
        last.next = new_node  # type: ignore

    def delete(self, key):
        temp = self.head
        if temp is not None:
            if temp.data["id"] == key:
                self.head = temp.next
                return
        while temp is not None:
            if temp.data["id"] == key:
                break
            prev = temp
            temp = temp.next
        if temp is None:
            return
        prev.next = temp.next

    def get_all(self):
        schedule = []
        current = self.head
        while current:
            schedule.append(current.data)
            current = current.next
        return schedule


class Schedule:
    def __init__(self):
        self.classes = LinkedList()

    def add_class(self, class_data):
        self.classes.append(class_data)

    def delete_class(self, class_id):
        self.classes.delete(class_id)

    def get_schedule(self):
        return self.classes.get_all()

    def search_classes(self, **kwargs):
        all_classes = self.get_schedule()
        filtered_classes = []
        for cls in all_classes:
            match = all(
                cls.get(key) == value for key, value in kwargs.items() if value
            )
            if match:
                filtered_classes.append(cls)
        return filtered_classes


schedule_manager = Schedule()


def _generate_sample_data(num_classes=10):
    fake = Faker()
    for _ in range(num_classes):
        class_id = len(schedule_manager.get_schedule()) + 1
        new_class = {
            "id": class_id,
            "group_name": fake.word().title(),
            "teacher_name": fake.name(),
            "classroom": random.randint(100, 300),
            "date": fake.date_between(
                start_date="-30d", end_date="+30d"
            ).strftime("%Y-%m-%d"),
            "time": fake.time(),
        }
        schedule_manager.add_class(new_class)


_generate_sample_data(100)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, token: str = Cookie(None)):
    user = None
    if token:
        user = decode_jwt(token)
        if user and user.get("exp", 0) < time.time():
            user = None

    return templates.TemplateResponse(
        "index.html", {"request": request, "user": user}
    )


@app.get("/add_class", response_class=HTMLResponse)
async def add_class_form(request: Request, token: str = Cookie(None)):
    user = None
    if token:
        user = decode_jwt(token)
        if user and user.get("exp", 0) < time.time():
            user = None

    return templates.TemplateResponse(
        "add_class.html", {"request": request, "message": "", "user": user}
    )


@app.post("/add_class")
async def add_class(
    request: Request,
    group_name: str = Form(...),
    teacher_name: str = Form(...),
    classroom: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    user=Depends(require_role("teacher", "admin")),
):
    class_id = len(schedule_manager.get_schedule()) + 1
    new_class = {
        "id": class_id,
        "group_name": group_name,
        "teacher_name": teacher_name,
        "classroom": classroom,
        "date": date,
        "time": time,
    }
    schedule_manager.add_class(new_class)
    return templates.TemplateResponse(
        "add_class.html",
        {"request": request, "message": "Занятие успешно добавлено!"},
    )


@app.get("/view_schedule", response_class=HTMLResponse)
async def view_schedule(request: Request, token: str = Cookie(None)):
    user = None
    if token:
        user = decode_jwt(token)
        if user and user.get("exp", 0) < time.time():
            user = None

    classes = schedule_manager.get_schedule()
    return templates.TemplateResponse(
        "view_schedule.html",
        {"request": request, "classes": classes, "user": user},
    )


@app.get("/search_class", response_class=HTMLResponse)
async def search_class_form(request: Request, token: str = Cookie(None)):
    user = None
    if token:
        user = decode_jwt(token)
        if user and user.get("exp", 0) < time.time():
            user = None

    return templates.TemplateResponse(
        "search_class.html", {"request": request, "message": "", "user": user}
    )


@app.post("/search_class")
async def search_class(
    request: Request,
    group_name: str = Form(None),
    teacher_name: str = Form(None),
    classroom: str = Form(None),
    date: str = Form(None),
    time: str = Form(None),
):
    class_info = schedule_manager.search_classes(
        group_name=group_name,
        teacher_name=teacher_name,
        classroom=classroom,
        date=date,
        time=time,
    )
    return templates.TemplateResponse(
        "search_class.html",
        {
            "request": request,
            "class_info": class_info,
            "message": "Занятия найдены!"
            if class_info
            else "Занятия не найдены",
        },
    )


@app.post("/delete_class")
async def delete_class(
    request: Request,
    class_id: int = Form(...),
    user=Depends(require_role("admin", "teacher")),
):
    schedule_manager.delete_class(class_id)
    return RedirectResponse("/view_schedule", status_code=303)


@app.get("/statistics", response_class=HTMLResponse)
async def show_statistics(request: Request, token: str = Cookie(None)):
    user = None
    if token:
        user = decode_jwt(token)
        if user and user.get("exp", 0) < time.time():
            user = None

    classes = schedule_manager.get_schedule()
    stats = {
        "total_classes": len(classes),
        "unique_teachers": len(set(cls["teacher_name"] for cls in classes)),
        "unique_groups": len(set(cls["group_name"] for cls in classes)),
        "unique_classrooms": len(set(cls["classroom"] for cls in classes)),
    }
    return templates.TemplateResponse(
        "statistics.html", {"request": request, "stats": stats, "user": user}
    )
