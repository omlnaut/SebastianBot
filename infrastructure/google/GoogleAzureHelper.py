from google.oauth2.credentials import Credentials

from infrastructure.google.GoogleSecret import GoogleSecret
from shared.secrets import SecretKeys, get_secret


def load_google_credentials() -> Credentials:
    credentials_model = get_secret(SecretKeys.GoogleCredentials, GoogleSecret)
    creds = Credentials.from_authorized_user_info(
        credentials_model.credentials.model_dump()
    )
    return creds
