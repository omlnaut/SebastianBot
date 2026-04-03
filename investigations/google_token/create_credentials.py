# pyright: standard
import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

# The scopes required
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar",
]


def main():
    # stored in bitwarden
    current_dir = Path(__file__).resolve().parent
    creds_path = current_dir / "credentials.json"

    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
    creds = flow.run_local_server(port=0)
    creds_json = json.loads(creds.to_json())
    vault_dict = {"credentials": creds_json}

    # Save the credentials for the Cloud Function
    with open(current_dir / "logged_in_credentials.json", "w") as token:
        token.write(json.dumps(vault_dict))


if __name__ == "__main__":
    main()
