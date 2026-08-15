from pydantic import BaseModel


class DeepSeekApiKey(BaseModel):
    api_key: str
