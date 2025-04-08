from pydantic import BaseModel


class Options(BaseModel):
    id: int
    text: str
    next_question: int | str # str для значений NULL
    risk_type: str
    risk_value: int

class Questions(BaseModel):
    id: int
    text: str
    type: str
    required: bool
    is_conditional: bool
    options: list[Options]
