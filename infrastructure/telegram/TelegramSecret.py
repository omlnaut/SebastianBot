from typing import Dict

from pydantic import BaseModel


class Chat(BaseModel):
    id: int


class Token(BaseModel):
    token: str


class TelegramConfig(BaseModel):
    chats: Dict[str, Chat]
    tokens: Dict[str, Token]
