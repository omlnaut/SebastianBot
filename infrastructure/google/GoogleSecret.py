from pydantic import BaseModel
from typing import List


class Credentials(BaseModel):
    token: str
    refresh_token: str
    token_uri: str
    client_id: str
    client_secret: str
    scopes: List[str]
    universe_domain: str
    account: str
    expiry: str


class GoogleSecret(BaseModel):
    credentials: Credentials
