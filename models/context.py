from pydantic import BaseModel
from config import Languages


class UserContext(BaseModel):
    city: str
    language: Languages
    name: str
    comment: str
