from pydantic import BaseModel


class MietplanCredentials(BaseModel):
    username: str
    password: str
