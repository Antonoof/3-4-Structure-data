from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any
from faker import Faker
import random

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

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
        last.next = new_node

    def delete(self, key):
        temp = self.head
        if temp is not None:
            if temp.data["id"] == key:
                self.head = temp.next
                temp = None
                return
        while temp is not None:
            if temp.data["id"] == key:
                break
            prev = temp
            temp = temp.next
        if temp == None:
            return
        prev.next = temp.next
        temp = None

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
            match = all(cls.get(key) == value for key, value in kwargs.items() if value)
            if match:
                filtered_classes.append(cls)
        return filtered_classes

schedule_manager = Schedule()

def generate_sample_data(num_classes=10):
    fake = Faker()
    for _ in range(num_classes):
        class_id = len(schedule_manager.get_schedule()) + 1
        new_class = {
            "id": class_id,
            "group_name": fake.word().title(),
            "teacher_name": fake.name(),
            "classroom": random.randint(100, 300),
            "date": fake.date_between(start_date='-30d', end_date='+30d').strftime("%Y-%m-%d"),
            "time": fake.time()
        }
        schedule_manager.add_class(new_class)

generate_sample_data(100)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/add_class", response_class=HTMLResponse)
async def add_class_form(request: Request):
    return templates.TemplateResponse("add_class.html", {"request": request, "message": ""})

@app.post("/add_class")
async def add_class(request: Request, group_name: str = Form(...), teacher_name: str = Form(...), classroom: str = Form(...), date: str = Form(...), time: str = Form(...)):
    class_id = len(schedule_manager.get_schedule()) + 1
    new_class = {
        "id": class_id,
        "group_name": group_name,
        "teacher_name": teacher_name,
        "classroom": classroom,
        "date": date,
        "time": time
    }
    schedule_manager.add_class(new_class)
    return templates.TemplateResponse("add_class.html", {"request": request, "message": "Занятие успешно добавлено!"})

@app.get("/view_schedule", response_class=HTMLResponse)
async def view_schedule(request: Request):
    classes = schedule_manager.get_schedule()
    return templates.TemplateResponse("view_schedule.html", {"request": request, "classes": classes})

@app.get("/search_class", response_class=HTMLResponse)
async def search_class_form(request: Request):
    return templates.TemplateResponse("search_class.html", {"request": request, "message": ""})

@app.post("/search_class")
async def search_class(request: Request, group_name: str = Form(None), teacher_name: str = Form(None), classroom: str = Form(None), date: str = Form(None), time: str = Form(None)):
    class_info = schedule_manager.search_classes(group_name=group_name, teacher_name=teacher_name, classroom=classroom, date=date, time=time)
    return templates.TemplateResponse("search_class.html", {"request": request, "class_info": class_info, "message": "Занятия найдены!" if class_info else "Занятия не найдены"})

@app.post("/delete_class")
async def delete_class(request: Request, class_id: int = Form(...)):
    schedule_manager.delete_class(class_id)
    return RedirectResponse("/view_schedule", status_code=303)