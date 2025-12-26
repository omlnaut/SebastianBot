from pydantic import BaseModel


class GeminiApiKey(BaseModel):
    api_key: str
