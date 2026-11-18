# pyright: standard
import argparse
import json
import os
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks-only", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    # stored in bitwarden
    current_dir = Path(__file__).resolve().parent
    creds_path = current_dir / "credentials.json"

    scopes = ["https://www.googleapis.com/auth/tasks"] if args.tasks_only else SCOPES
    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), scopes)
    creds = flow.run_local_server(port=0)
    creds_json = json.loads(creds.to_json())
    vault_dict = {"credentials": creds_json}

    # Save the credentials for the Cloud Function
    output = args.output or current_dir / "logged_in_credentials.json"
    flags = os.O_WRONLY | os.O_CREAT | (os.O_EXCL if args.output else os.O_TRUNC)
    with os.fdopen(os.open(output, flags, 0o600), "w") as token:
        token.write(json.dumps(vault_dict))


if __name__ == "__main__":
    main()
