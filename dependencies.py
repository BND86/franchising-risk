import aiosqlite
from fastapi import Depends

from db import get_survey_db, get_responses_db
from repo import UserRepository, Repository


# эта функция внедряется в эндпоинт через Depends
async def get_user_repo(
    survey_db: aiosqlite.Connection = Depends(get_survey_db),
    responses_db: aiosqlite.Connection = Depends(get_responses_db)
) -> Repository:
    return UserRepository(survey_db, responses_db)
