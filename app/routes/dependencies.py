import aiosqlite
from fastapi import Depends

from app.db.db import get_survey_db, get_owner_db
from app.db.repo import UserRepository, OwnerRepository,  Repository


# эта функция внедряется в эндпоинт через Depends
async def get_user_repo(
        survey_db: aiosqlite.Connection = Depends(get_survey_db)
) -> Repository:
    return UserRepository(survey_db)

async def get_owner_repo(
        owner_db: aiosqlite.Connection = Depends(get_owner_db)
) -> Repository:
    return OwnerRepository(owner_db)
