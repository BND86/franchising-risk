from abc import ABC, abstractmethod
import aiosqlite
import aiofiles

from schemas import Questions, Options


class Repository(ABC): # интерфейс для опросника
    @abstractmethod
    async def get_questions() -> list[Questions]:
        pass

    @abstractmethod
    async def save_response():
        pass

class OwnerRepository(Repository): # для правообладателя
    pass

class UserRepository(Repository): # для франчайзи
    def __init__(self, survey_db: aiosqlite.Connection, responses_db: aiosqlite.Connection):
        self.survey_db = survey_db
        self.responses_db = responses_db

    async def get_questions(self) -> list[Questions]:
        cursor = await self.survey_db.cursor()
        await cursor.execute("SELECT id, question_text, question_type, is_required, is_conditional, categ FROM questions")
        questions = await cursor.fetchall()

        result = []
        for q in questions:
            await cursor.execute("SELECT id, option_text, next_question, risk_type, recomendations FROM options WHERE question_id=?", (q[0],))
            options = await cursor.fetchall()
            result.append(Questions(
                id=q[0],
                text=q[1],
                type=q[2],
                required=bool(q[3]),
                is_conditional=bool(q[4]),
                categ=(q[5]),
                options=[Options(id=opt[0],
                                 text=opt[1],
                                 next_question=opt[2],
                                 risk_type=opt[3],
                                 recomendations=opt[4]) for opt in options]
            ))

        return result
    
    async def save_response(self, session_id: str, question_id: int, option_id: int, risk_type: str, recomendations: int):
        cursor = await self.responses_db.cursor()
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                id_question INTEGER,
                id_option INTEGER,
                risk_type TEXT,
                recomendations TEXT
            )
        ''')
        
        await cursor.execute("INSERT INTO responses (session_id, id_question, id_option, risk_type, recomendations) VALUES (?, ?, ?, ?, ?)",
                    (session_id, question_id, option_id, risk_type, recomendations))
        await self.responses_db.commit()
        
        # временно переделал в асинхронную запись, это как правило дольше, но для маленького файла норм
        # потом можно будет вынести в BackgroundTasks синхронную функцию
        async with aiofiles.open("responses.txt", "a") as f:
            await f.write(f"{session_id}, {question_id}, {option_id}, {risk_type}, {recomendations}\n")
