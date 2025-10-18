from pydantic import BaseModel


class GoogleSecret(BaseModel):
    credentials: str
