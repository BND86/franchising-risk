import sqlite3
from fastapi import FastAPI, Form, Request, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from fastapi.responses import RedirectResponse

from repo import Repository
from dependencies import get_user_repo


app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
templates = Jinja2Templates(directory="templates")

DATABASE = "responses.db"

def get_risk_statistics(session_id: str):
    query = """
    SELECT 
        risk_type,
        COUNT(*) AS count_answers,
        SUM(risk_value) AS total_risk_value
    FROM responses
    WHERE session_id = ?
    GROUP BY risk_type;
    """
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (session_id,))
        data = cursor.fetchall()
    
    result = {"hight": {"count": 0, "sum": 0}, 
              "middle": {"count": 0, "sum": 0}, 
              "low": {"count": 0, "sum": 0}}
    
    for risk_type, count, total in data:
        if risk_type in result:
            result[risk_type] = {"count": count, "sum": total}
    
    return result

def get_session_id(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid4())  # Генерация нового уникального идентификатора
    return session_id

# Роуты для страниц
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/user", response_class=HTMLResponse)
async def survey_page(request: Request,
                      repo: Repository = Depends(get_user_repo)):
    session_id = get_session_id(request)  # Получаем сессию пользователя
    questions = await repo.get_questions()  # Acинхронная работа с базой данных
    return templates.TemplateResponse("user.html", {"request": request, "questions": questions, "session_id": session_id})

@app.get("/owner", response_class=HTMLResponse)
async def read_owner(request: Request):
    return templates.TemplateResponse("owner.html", {"request": request})

@app.get("/glossary")
async def read_glossary(request: Request):
    return templates.TemplateResponse("glossary.html", {"request": request})

@app.get("/stats.html")
def index(request: Request, session_id: str = Query(None, description="Session ID to filter responses")):
    if not session_id:
        return templates.TemplateResponse("stats.html", {"request": request, "stats": None, "session_id": None})
    
    stats = get_risk_statistics(session_id)
    return templates.TemplateResponse("stats.html", {"request": request, "stats": stats, "session_id": session_id})

@app.post("/submit")
async def submit_survey(request: Request,
                        repo: Repository = Depends(get_user_repo)):
    form_data = await request.form()
    session_id = get_session_id(request)  # Идентификатор сессии пользователя    
    # Обработка данных формы
    for key, value in form_data.items():
        if "_" in key:  # id вопроса и id ответа
            question_id, option_id = map(int, key.split("_"))
            risk_type, risk_value = value.split(",")
            await repo.save_response(session_id, question_id, option_id, risk_type, int(risk_value))  # Асинхронная запись
    
    # После обработки данных перенаправляем пользователя на страницу /stats.html
    return RedirectResponse(url=f"/stats.html?session_id={session_id}", status_code=303)

