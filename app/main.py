import sqlite3
from fastapi import FastAPI, Form, Request, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from fastapi.responses import RedirectResponse, FileResponse

from app.db.repo import Repository
from app.db.db import OWNER_DB, SURVEY_DB
from app.routes.dependencies import get_user_repo, get_owner_repo
from app.services.make_pdf import make_pdf

from typing import Optional
from pydantic import BaseModel
from app.services.calculator import calculate_results


app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")
templates = Jinja2Templates(directory="app/templates")

class InputData(BaseModel):
    start_investment: float = 1_300_000
    franchise_fee: float = 350_000
    royalty_percent: float = 2
    payback_period: float = 12
    monthly_turnover: float = 900_000

    pedestrian_traffic: float = 190_000
    car_traffic: float = 90_000
    competitors_count: float = 447
    search_queries: float = 1_135_000

    operational_expenses: float = 50
    additional_payments: float = 10



# Словарь для перевода типов рисков на русский язык
RISK_TRANSLATIONS = {
    "high": "Высокий риск",
    "medium": "Средний риск",
    "low": "Незначительный риск",
    "significant": "Существенный риск"
}

def get_risk_statistics(session_id: str):
    # Подключение к базе данных survey.db для вопросов и вариантов ответов
    with sqlite3.connect(SURVEY_DB) as conn:
        cursor = conn.cursor()
        
        # Получаем все вопросы с категориями
        cursor.execute("SELECT id, question_text, categ FROM questions")
        questions = {q[0]: {"text": q[1], "categ": q[2] or "Без категории"} for q in cursor.fetchall()}

        # Получаем все варианты ответа
        cursor.execute("SELECT id, option_text FROM options")
        options = {option[0]: option[1] for option in cursor.fetchall()}

        # Получаем ответы с рисками для указанной сессии
        cursor.execute("""
        SELECT r.risk_type, r.recomendations, r.article, r.link, r.id_question, r.id_option 
        FROM responses r
        WHERE r.session_id = ? AND r.risk_type IS NOT NULL AND r.risk_type != ''
        """, (session_id,))
        responses = cursor.fetchall()

    # Инициализация структуры результатов
    risk_types = ["significant", "high", "medium", "low"]
    result = {
        "total_risks": 0,
        "by_risk_type": {rt: {
            "count": 0,
            "recomendations": [],
            "article": [],
            "link": [],
            "details": []
        } for rt in risk_types},
        "by_category": {}
    }

    # Обработка ответов
    for risk_type, recs, article, link, q_id, opt_id in responses:
        # Проверяем, что тип риска допустимый
        if risk_type not in risk_types:
            continue

        question = questions.get(q_id, {})
        option_text = options.get(opt_id, "Неизвестный вариант")
        category = question.get("categ", "Без категории")

        # Подготовка данных
        rec_list = [r.strip() for r in recs.split(",")] if recs else []
        article_list = [a.strip() for a in article.split(",")] if article else []
        link_list = [l.strip() for l in link.split(",")] if link else []

        # Обновляем общую статистику
        result["total_risks"] += 1

        # Обновляем статистику по типу риска
        risk_stats = result["by_risk_type"][risk_type]
        risk_stats["count"] += 1
        risk_stats["recomendations"].extend(rec_list)
        risk_stats["article"].extend(article_list)
        risk_stats["link"].extend(link_list)
        risk_stats["details"].append({
            "question": question.get("text", "Неизвестный вопрос"),
            "answer": option_text,
            "recomendations": rec_list,
            "article": article_list,
            "link": link_list
        })

        # Обновляем статистику по категории
        if category not in result["by_category"]:
            result["by_category"][category] = {
                "total": 0,
                **{rt: 0 for rt in risk_types}
            }
        
        result["by_category"][category]["total"] += 1
        result["by_category"][category][risk_type] += 1

    # Удаляем дубликаты в рекомендациях, статьях и ссылках
    for rt in risk_types:
        risk_stats = result["by_risk_type"][rt]
        risk_stats["recomendations"] = list(dict.fromkeys(risk_stats["recomendations"]))
        risk_stats["article"] = list(dict.fromkeys(risk_stats["article"]))
        risk_stats["link"] = list(dict.fromkeys(risk_stats["link"]))

    return result


def get_risk_statistics_owner(session_id: str):
    # Подключение к базе данных owner.db для вопросов и вариантов ответов
    with sqlite3.connect(OWNER_DB) as conn:
        cursor = conn.cursor()
        
        # Получаем все вопросы с категориями
        cursor.execute("SELECT id, question_text, categ FROM questions")
        questions = {q[0]: {"text": q[1], "categ": q[2] or "Без категории"} for q in cursor.fetchall()}

        # Получаем все варианты ответа
        cursor.execute("SELECT id, option_text FROM options")
        options = {option[0]: option[1] for option in cursor.fetchall()}

        # Получаем ответы с рисками для указанной сессии
        cursor.execute("""
        SELECT r.risk_type, r.recomendations, r.article, r.link, r.id_question, r.id_option 
        FROM responses r
        WHERE r.session_id = ? AND r.risk_type IS NOT NULL AND r.risk_type != ''
        """, (session_id,))
        responses = cursor.fetchall()

    # Инициализация структуры результатов
    risk_types = ["significant", "high", "medium", "low"]
    result = {
        "total_risks": 0,
        "by_risk_type": {rt: {
            "count": 0,
            "recomendations": [],
            "article": [],
            "link": [],
            "details": []
        } for rt in risk_types},
        "by_category": {}
    }

    # Обработка ответов
    for risk_type, recs, article, link, q_id, opt_id in responses:
        # Проверяем, что тип риска допустимый
        if risk_type not in risk_types:
            continue

        question = questions.get(q_id, {})
        option_text = options.get(opt_id, "Неизвестный вариант")
        category = question.get("categ", "Без категории")

        # Подготовка данных
        rec_list = [r.strip() for r in recs.split(",")] if recs else []
        article_list = [a.strip() for a in article.split(",")] if article else []
        link_list = [l.strip() for l in link.split(",")] if link else []

        # Обновляем общую статистику
        result["total_risks"] += 1

        # Обновляем статистику по типу риска
        risk_stats = result["by_risk_type"][risk_type]
        risk_stats["count"] += 1
        risk_stats["recomendations"].extend(rec_list)
        risk_stats["article"].extend(article_list)
        risk_stats["link"].extend(link_list)
        risk_stats["details"].append({
            "question": question.get("text", "Неизвестный вопрос"),
            "answer": option_text,
            "recomendations": rec_list,
            "article": article_list,
            "link": link_list
        })

        # Обновляем статистику по категории
        if category not in result["by_category"]:
            result["by_category"][category] = {
                "total": 0,
                **{rt: 0 for rt in risk_types}
            }
        
        result["by_category"][category]["total"] += 1
        result["by_category"][category][risk_type] += 1

    # Удаляем дубликаты в рекомендациях, статьях и ссылках
    for rt in risk_types:
        risk_stats = result["by_risk_type"][rt]
        risk_stats["recomendations"] = list(dict.fromkeys(risk_stats["recomendations"]))
        risk_stats["article"] = list(dict.fromkeys(risk_stats["article"]))
        risk_stats["link"] = list(dict.fromkeys(risk_stats["link"]))

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
async def read_owner(request: Request,
                      repo: Repository = Depends(get_owner_repo)):
    session_id = get_session_id(request)  # Получаем сессию пользователя
    questions = await repo.get_questions()  # Асинхронная работа с базой данных
    return templates.TemplateResponse("owner.html", {"request": request, "questions": questions, "session_id": session_id})
    #return templates.TemplateResponse("owner.html", {"request": request})

@app.get("/glossary")
async def read_glossary(request: Request):
    return templates.TemplateResponse("glossary.html", {"request": request})

@app.get("/stats.html")
def index(request: Request, session_id: str = Query(None, description="Session ID to filter responses")):
    if not session_id:
        return templates.TemplateResponse("stats.html", {"request": request, "stats": None, "session_id": None, "risk_translations": RISK_TRANSLATIONS})
    
    stats = get_risk_statistics(session_id)
    return templates.TemplateResponse("stats.html", {"request": request, "stats": stats, "session_id": session_id, "risk_translations": RISK_TRANSLATIONS})

@app.get("/stats_owner.html")
def index(request: Request, session_id: str = Query(None, description="Session ID to filter responses")):
    if not session_id:
        return templates.TemplateResponse("stats_owner.html", {"request": request, "stats": None, "session_id": None, "risk_translations": RISK_TRANSLATIONS})
    
    stats = get_risk_statistics_owner(session_id)
    return templates.TemplateResponse("stats_owner.html", {"request": request, "stats": stats, "session_id": session_id, "risk_translations": RISK_TRANSLATIONS})


@app.post("/submit")
async def submit_survey(request: Request,
                       repo: Repository = Depends(get_user_repo)):
    form_data = await request.form()
    session_id = get_session_id(request)
    
    print("\n=== Received form submission ===")
    print(f"Session ID: {session_id}")
    print("Form data:")
    for key, value in form_data.items():
        print(f"  {key}: {value}")
    
    # Обработка данных формы
    for key, value in form_data.items():
        if key.startswith('q'):  
            question_id = int(key[1:])
            option_id, risk_type, recomendations, article, link = value.split("|")
            print(f"Processing question {question_id}, option {option_id}")
            await repo.save_response(session_id, question_id, option_id, risk_type, recomendations, article, link)

    print("=== Form processing completed ===")
    return RedirectResponse(url=f"/stats.html?session_id={session_id}", status_code=303)

@app.post("/submit_owner")
async def submit_survey_owner(request: Request,
                        repo: Repository = Depends(get_owner_repo)):
    form_data = await request.form()
    session_id = get_session_id(request)
    
    print("\n=== Received form submission ===")
    print(f"Session ID: {session_id}")
    print("Form data:")
    for key, value in form_data.items():
        print(f"  {key}: {value}")
    
    # Обработка данных формы
    for key, value in form_data.items():
        if key.startswith('q'):  
            question_id = int(key[1:])
            option_id, risk_type, recomendations, article, link = value.split("|")
            print(f"Processing question {question_id}, option {option_id}")
            await repo.save_response(session_id, question_id, option_id, risk_type, recomendations, article, link)

    print("=== Form processing completed ===")
    return RedirectResponse(url=f"/stats_owner.html?session_id={session_id}", status_code=303)

@app.get("/economic")
async def economic_page(request: Request):
    return templates.TemplateResponse("economic.html", {"request": request})

@app.post("/result")
async def result_page(
    request: Request,
    start_investment: float = Form(default=1_300_000),
    franchise_fee: float = Form(default=350_000),
    royalty_percent: float = Form(default=2),
    payback_period: float = Form(default=12),
    monthly_turnover: float = Form(default=900_000),
    pedestrian_traffic: float = Form(default=190_000),
    car_traffic: float = Form(default=90_000),
    competitors_count: float = Form(default=447),
    search_queries: float = Form(default=1_135_000),
    operational_expenses: float = Form(default=50),
    additional_payments: float = Form(default=10),
):
    input_data = InputData(
        start_investment=start_investment,
        franchise_fee=franchise_fee,
        royalty_percent=royalty_percent,
        payback_period=payback_period,
        monthly_turnover=monthly_turnover,
        pedestrian_traffic=pedestrian_traffic,
        car_traffic=car_traffic,
        competitors_count=competitors_count,
        search_queries=search_queries,
        operational_expenses=operational_expenses,
        additional_payments=additional_payments,
    )
    results = calculate_results(input_data.dict())
    return templates.TemplateResponse("result_econom.html", {"request": request, "results": results})

@app.get("/download/")
async def download(response_class=FileResponse,
                   session_id: str = Query(None, description="Session ID to filter responses")):
    stats = get_risk_statistics(session_id)
    file_path = make_pdf(stats, session_id)
    return FileResponse(path=file_path, filename="risk_report.pdf", media_type='application/pdf')


@app.post("/test-submit")
async def test_submit(request: Request):
    form_data = await request.form()
    print("\n=== Received form data ===")
    for key, value in form_data.items():
        print(f"{key}: {value}")
    return {"status": "success"}