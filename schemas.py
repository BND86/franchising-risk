from pydantic import BaseModel
from typing import Optional


class Options(BaseModel):
    id: int
    text: str
    next_question: int | str # str для значений NULL
    risk_type: Optional[str] = None  
    recomendations: Optional[str] = None

class Questions(BaseModel):
    id: int
    text: str
    type: str
    required: bool
    is_conditional: bool
    options: list[Options]
