from pydantic import BaseModel


class BiboAccountCredentials(BaseModel):
    username: str
    password: str


class BiboCredentials(BaseModel):
    accounts: dict[str, BiboAccountCredentials]
