import sqlite3

SURVEY_DB = "survey.db"
RESPONSES_DB = "responses.db"

def get_questions():
    conn = sqlite3.connect(SURVEY_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, question_text, question_type, is_required, is_conditional, categ FROM questions")
    questions = cursor.fetchall()

    result = []
    for q in questions:
        cursor.execute("SELECT id, option_text, next_question, risk_type, recomendations, article, link FROM options WHERE question_id=?", (q[0],))
        options = cursor.fetchall()
        result.append({
            "id": q[0],
            "text": q[1],
            "type": q[2],
            "required": bool(q[3]),
            "is_conditional": bool(q[4]),  # Преобразуем в boolean
            "options": [{"id": opt[0], "text": opt[1], "next_question": opt[2], "risk_type": opt[3], "recomendations": opt[4], "article": opt[5], "link": opt[6]} for opt in options]
        })
    
    conn.close()
    return result


def save_response(session_id, question_id, option_id, risk_type, recomendations, article, link):
    conn = sqlite3.connect(RESPONSES_DB)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            id_question INTEGER,
            id_option INTEGER,
            risk_type TEXT,
            recomendations TEXT,
            article TEXT,
            link TEXT
        )
    ''')
    
    cursor.execute("INSERT INTO responses (session_id, id_question, id_option, risk_type, recomendations, article, link) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (session_id, question_id, option_id, risk_type, recomendations, article, link))
    conn.commit()
    conn.close()

    with open("responses.txt", "a") as f:
        f.write(f"{session_id}, {question_id}, {option_id}, {risk_type}, {recomendations}, {article}, {link}\n")
