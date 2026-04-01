from functools import lru_cache

from google.oauth2.credentials import Credentials

from cloud.helper import SecretKeys, get_secret


@lru_cache()
def load_google_credentials() -> Credentials:
    credentials_model = get_secret(SecretKeys.GoogleCredentials)
    creds = Credentials.from_authorized_user_info(credentials_model.credentials.model_dump())  # type: ignore
    return creds
