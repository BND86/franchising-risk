import sqlite3
import json
from fastapi import FastAPI, Form, Request, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from fastapi.responses import RedirectResponse, FileResponse

from repo import Repository
from dependencies import get_user_repo


app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
templates = Jinja2Templates(directory="templates")

DATABASE = "responses.db"

# Словарь для перевода типов рисков на русский язык
RISK_TRANSLATIONS = {
    "high": "Высокий риск",
    "medium": "Средний риск",
    "low": "Незначительный риск",
    "significant": "Существенный риск"
}

def get_risk_statistics(session_id: str):
    # Подключение к базе данных survey.db для вопросов и вариантов ответов
    with sqlite3.connect("survey.db") as conn_survey:
        cursor_survey = conn_survey.cursor()
        # Запрос на получение всех вопросов с категориями
        cursor_survey.execute("""
        SELECT id, question_text, categ FROM questions
        """)
        questions = {q[0]: {"text": q[1], "categ": q[2]} for q in cursor_survey.fetchall()}

        # Запрос на получение всех вариантов ответа
        cursor_survey.execute("""
        SELECT id, option_text FROM options
        """)
        options = {option[0]: option[1] for option in cursor_survey.fetchall()}

    # Подключение к базе данных responses.db для ответов и рекомендаций
    with sqlite3.connect("survey.db") as conn_responses:
        cursor_responses = conn_responses.cursor()
        # Запрос для получения всех ответов и рекомендаций для указанной сессии
        cursor_responses.execute("""
        SELECT r.risk_type, r.recomendations, r.id_question, r.id_option 
        FROM responses r
        WHERE r.session_id = ?
        """, (session_id,))
        responses = cursor_responses.fetchall()

    # Структура для хранения статистики
    result = {
        "total_risks": 0,
        "by_risk_type": {
            "significant": {"count": 0, "recommendations": [], "details": []},
            "high": {"count": 0, "recommendations": [], "details": []}, 
            "medium": {"count": 0, "recommendations": [], "details": []},
            "low": {"count": 0, "recommendations": [], "details": []}
        },
        "by_category": {}
    }

    # Обработка данных
    for risk_type, recomendations, question_id, option_id in responses:
        question = questions.get(question_id)
        if not question:
            continue
            
        question_text = question["text"]
        category = question["categ"] or "Без категории"
        option_text = options.get(option_id, "Неизвестный вариант")
        
        # Обновляем общее количество рисков
        result["total_risks"] += 1
        
        # Обновляем статистику по типам рисков
        if risk_type in result["by_risk_type"]:
            result["by_risk_type"][risk_type]["count"] += 1
            result["by_risk_type"][risk_type]["recommendations"].extend(recomendations.split(","))
            result["by_risk_type"][risk_type]["details"].append({
                "question": question_text,
                "answer": option_text,
                "recommendations": recomendations.split(",")
            })
        
        # Обновляем статистику по категориям
        if category not in result["by_category"]:
            result["by_category"][category] = {
                "total": 0,
                "significant": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        
        result["by_category"][category]["total"] += 1
        if risk_type in result["by_category"][category]:
            result["by_category"][category][risk_type] += 1

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
async def user_page(request: Request):
    return templates.TemplateResponse("user.html", {"request": request})

@app.get("/contract", response_class=HTMLResponse)
async def survey_page(request: Request,
                      repo: Repository = Depends(get_user_repo)):
    session_id = get_session_id(request)  # Получаем сессию пользователя
    questions = await repo.get_questions()  # Асинхронная работа с базой данных
    return templates.TemplateResponse("contract.html", {"request": request, "questions": questions, "session_id": session_id})

@app.get("/owner", response_class=HTMLResponse)
async def read_owner(request: Request):
    return templates.TemplateResponse("owner.html", {"request": request})

@app.get("/glossary")
async def read_glossary(request: Request):
    return templates.TemplateResponse("glossary.html", {"request": request})

@app.get("/stats.html")
def index(request: Request, session_id: str = Query(None, description="Session ID to filter responses")):
    if not session_id:
        return templates.TemplateResponse("stats.html", {"request": request, "stats": None, "session_id": None, "risk_translations": RISK_TRANSLATIONS})
    
    stats = get_risk_statistics(session_id)
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4, ensure_ascii=False)
    return templates.TemplateResponse("stats.html", {"request": request, "stats": stats, "session_id": session_id, "risk_translations": RISK_TRANSLATIONS})

@app.post("/submit")
async def submit_survey(request: Request,
                        repo: Repository = Depends(get_user_repo)):
    form_data = await request.form()
    session_id = get_session_id(request)  # Идентификатор сессии пользователя    
    # Обработка данных формы
    for key, value in form_data.items():
        if "_" in key:  # id вопроса и id ответа
            question_id, option_id = map(int, key.split("_"))
            risk_type, recomendations = value.split("_")
            await repo.save_response(session_id, question_id, option_id, risk_type, recomendations)  # Асинхронная запись
    
    # После обработки данных перенаправляем пользователя на страницу /stats.html
    return RedirectResponse(url=f"/stats.html?session_id={session_id}", status_code=303)

# @app.get("/stats/download")
# async def download(response_class=FileResponse,
#                    file = Depends(page_to_pdf)):
    