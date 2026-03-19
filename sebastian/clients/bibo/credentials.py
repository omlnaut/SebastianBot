from pydantic import BaseModel


class BiboCredentials(BaseModel):
    username: str
    password: str
