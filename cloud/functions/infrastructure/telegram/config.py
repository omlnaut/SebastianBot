from pydantic import BaseModel


class Chat(BaseModel):
    id: int


class Token(BaseModel):
    token: str


class TelegramConfig(BaseModel):
    chats: dict[str, Chat]
    tokens: dict[str, Token]


class TelegramToken:
    Sebastian = "Sebastian"


class TelegramChat:
    MainChat = "mainChat"
