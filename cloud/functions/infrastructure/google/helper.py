from google.oauth2.credentials import Credentials

from cloud.helper import SecretKeys, get_secret

from .credentials import GoogleSecret


def load_google_credentials() -> Credentials:
    credentials_model = get_secret(SecretKeys.GoogleCredentials, GoogleSecret)
    creds = Credentials.from_authorized_user_info(
        credentials_model.credentials.model_dump()
    )
    return creds
