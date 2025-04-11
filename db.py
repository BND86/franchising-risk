import aiosqlite


SURVEY_DB = "survey.db"
OWNER_DB = "owner.db"
# функции выдают подключение и закрываеют его, когда перестают использоваться
async def get_survey_db():
    conn = await aiosqlite.connect(SURVEY_DB)
    try:
        yield conn
    finally:
        await conn.close()

async def get_owner_db():
    conn = await aiosqlite.connect(OWNER_DB)
    try:
        yield conn
    finally:
        await conn.close()
