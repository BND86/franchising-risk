from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import get_questions, save_response


app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def survey_page(request: Request):
    questions = get_questions()
    return templates.TemplateResponse("survey.html", {"request": request, "questions": questions})

@app.post("/submit")
async def submit_survey(request: Request):
    form_data = await request.form()
    for key, value in form_data.items():
        if "_" in key:  # id вопроса и id ответа
            question_id, option_id = map(int, key.split("_"))
            risk_type, risk_value = value.split(",")
            save_response(question_id, option_id, risk_type, int(risk_value))
    
    return {"message": "Ответы успешно сохранены!"}
