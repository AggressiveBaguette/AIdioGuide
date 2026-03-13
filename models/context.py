from pydantic import BaseModel


class UserContext(BaseModel):
    city: str
    language: str
    name: str
    comment: str
