from pydantic import BaseModel

# todo: remove google genai package


class DeepSeekApiKey(BaseModel):
    api_key: str
