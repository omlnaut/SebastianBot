from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

# The scopes required
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/drive",
]


def main():
    # stored in bitwarden
    current_dir = Path(__file__).resolve().parent
    creds_path = current_dir / "credentials.json"

    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
    creds = flow.run_local_server(port=0)

    # Save the credentials for the Cloud Function
    with open(current_dir / "logged_in_credentials.json", "w") as token:
        token.write(creds.to_json())


if __name__ == "__main__":
    main()
