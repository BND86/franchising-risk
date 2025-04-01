from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import get_questions, save_response
from uuid import uuid4


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Функция для получения идентификатора сессии пользователя
def get_session_id(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid4())  # Генерация нового уникального идентификатора
    return session_id

@app.get("/", response_class=HTMLResponse)
async def survey_page(request: Request):
    session_id = get_session_id(request)  # Получаем сессию пользователя
    questions = get_questions()  # Синхронная работа с базой данных
    return templates.TemplateResponse("survey.html", {"request": request, "questions": questions, "session_id": session_id})

@app.post("/submit")
async def submit_survey(request: Request):
    form_data = await request.form()
    session_id = get_session_id(request)  # Идентификатор сессии пользователя    
    # Обработка данных формы
    for key, value in form_data.items():
        if "_" in key:  # id вопроса и id ответа
            question_id, option_id = map(int, key.split("_"))
            risk_type, risk_value = value.split(",")
            save_response(session_id, question_id, option_id, risk_type, int(risk_value))  # Синхронная запись
    
    return {"message": "Ответы успешно сохранены!"}
