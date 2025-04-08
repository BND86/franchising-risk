import aiosqlite


SURVEY_DB = "survey.db"
RESPONSES_DB = "responses.db"
# функции выдают подключение и закрываеют его, когда перестают использоваться
async def get_survey_db():
    conn = await aiosqlite.connect(SURVEY_DB)
    try:
        yield conn
    finally:
        await conn.close()

async def get_responses_db():
    conn = await aiosqlite.connect(RESPONSES_DB)
    try:
        yield conn
    finally:
        await conn.close()
