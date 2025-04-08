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
        # Запрос на получение всех вопросов
        cursor_survey.execute("""
        SELECT id, question_text FROM questions
        """)
        questions = cursor_survey.fetchall()

        # Запрос на получение всех вариантов ответа
        cursor_survey.execute("""
        SELECT id, option_text FROM options
        """)
        options = cursor_survey.fetchall()

    # Подключение к базе данных responses.db для ответов и рекомендаций
    with sqlite3.connect("responses.db") as conn_responses:
        cursor_responses = conn_responses.cursor()
        # Запрос для получения всех ответов и рекомендаций для указанной сессии
        cursor_responses.execute("""
        SELECT r.risk_type, r.recomendations, r.id_question, r.id_option 
        FROM responses r
        WHERE r.session_id = ?
        """, (session_id,))
        responses = cursor_responses.fetchall()

    # Структура для хранения статистики
    result = {"significant": {"count": 0, "recommendations": [], "details": []},
              "high": {"count": 0, "recommendations": [], "details": []}, 
              "medium": {"count": 0, "recommendations": [], "details": []},
              "low": {"count": 0, "recommendations": [], "details": []}}

    # Преобразуем список options в словарь для быстрого поиска
    options_dict = {option[0]: option[1] for option in options}

    # Обработка данных
    for risk_type, recomendations, question_id, option_id in responses:
        # Находим соответствующий вопрос
        question = next((q for q in questions if q[0] == question_id), None)
        if question:
            question_text = question[1]
            
            # Получаем текст варианта ответа из options_dict
            option_text = options_dict.get(option_id)

            # Добавляем информацию в соответствующий риск
            if risk_type in result:
                result[risk_type]["count"] += 1
                result[risk_type]["recommendations"].extend(recomendations.split(","))
                result[risk_type]["details"].append({
                    "question": question_text,
                    "answer": option_text,
                    "recommendations": recomendations.split(",")
                })

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
    questions = await repo.get_questions()  # Асинхронная работа с базой данных
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
        return templates.TemplateResponse("stats.html", {"request": request, "stats": None, "session_id": None, "risk_translations": RISK_TRANSLATIONS})
    
    stats = get_risk_statistics(session_id)
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
