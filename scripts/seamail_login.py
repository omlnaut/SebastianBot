#!/usr/bin/env python3
"""Authorise another Google account for `seamail` — headless-safe OAuth flow.

The existing `~/.seamail.credentials` is written by
`investigations/google_token/create_credentials.py`, which needs the OAuth
client's `credentials.json` (kept in Bitwarden) **and** a browser on the machine
that runs it. Neither is available on the Pi, so this script does two things
differently:

* it builds the client config from the `client_id`/`client_secret` that are
  already inside an existing `~/.seamail.credentials` (the OAuth app is the same
  one — only the account changes), and
* it never opens a browser and never binds a port: it prints the consent URL,
  waits for you to paste back the address your browser ended up on, and
  exchanges that for a refresh token.

Run it with the seamail virtualenv's interpreter (it has
`google-auth-oauthlib`):

    ~/.local/share/seamail/venv/bin/python \\
        ~/secretary/SebastianBot/scripts/seamail_login.py --name oli

The result is a separate file per account, so the accounts never overwrite each
other:

    SEAMAIL_GOOGLE_CREDENTIALS="$(cat ~/.seamail.credentials.oli)" seamail search 'livinghouse'

An existing file is only replaced when `--force` is given.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

# oauthlib refuses an http:// redirect on principle. The loopback redirect of a
# desktop OAuth client is http by definition (Google does not accept https on
# localhost), so this exemption is exactly what the RFC allows: it must happen
# before oauthlib is imported.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
# The granted scopes come back in the server's order, which trips oauthlib's
# scope-change warning. The scopes are the ones we asked for.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar",
]

DEFAULT_SOURCE = Path.home() / ".seamail.credentials"


def client_config_from(source: Path) -> dict:
    """Build an installed-app client config from an existing credentials file."""
    data = json.loads(source.read_text())
    inner = data.get("credentials", data)
    try:
        client_id = inner["client_id"]
        client_secret = inner["client_secret"]
    except KeyError as error:  # pragma: no cover - configuration error
        raise SystemExit(f"{source} has no {error.args[0]!r} — cannot reuse the OAuth app")
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def whoami(creds) -> str:
    """Ask Gmail whose mailbox was just authorised, as a self-check."""
    from googleapiclient.discovery import build

    profile = build("gmail", "v1", credentials=creds).users().getProfile(userId="me").execute()
    return profile.get("emailAddress", "unknown")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--name",
        required=True,
        help="label of the account, e.g. 'oli' → ~/.seamail.credentials.oli",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"credentials file whose OAuth client is reused (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument("--out", type=Path, help="output path (default: ~/.seamail.credentials.<name>)")
    parser.add_argument("--port", type=int, default=8765, help="loopback port in the redirect URI")
    parser.add_argument("--force", action="store_true", help="overwrite the output file if it exists")
    parser.add_argument(
        "--response",
        metavar="URL",
        help="the http://localhost… URL, instead of pasting it at the prompt",
    )
    args = parser.parse_args(argv)

    out = args.out or Path.home() / f".seamail.credentials.{args.name}"
    if out.exists() and not args.force:
        raise SystemExit(f"{out} exists — pass --force to replace it")

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_config(
        client_config_from(args.source),
        SCOPES,
        redirect_uri=f"http://localhost:{args.port}",
    )
    url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )

    print("\n1. Open this URL in a browser on any machine, and sign in with the")
    print("   account you want to add:\n")
    print(url)
    print(
        "\n2. The browser will end on a page that does not load — its address bar\n"
        f"   shows http://localhost:{args.port}/?state=...&code=... . That error is\n"
        "   expected: nothing is listening for it here.\n"
        "3. Copy that complete address and paste it below (the code is valid for\n"
        "   a few minutes and only once).\n"
    )
    response = args.response
    if response is None:
        response = input("Paste the full http://localhost… URL: ")
    response = response.strip()
    if not response:
        raise SystemExit("nothing pasted — aborted, nothing written")

    try:
        flow.fetch_token(authorization_response=response)
    except Exception as error:  # noqa: BLE001 - report, do not traceback at the user
        raise SystemExit(
            f"token exchange failed: {error}\n"
            "The authorisation code is single-use and short-lived — re-run the\n"
            "script and paste the address from that run, not an older one."
        ) from None
    creds = flow.credentials

    payload = {"credentials": json.loads(creds.to_json())}
    out.write_text(json.dumps(payload))
    out.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600

    account = whoami(creds)
    print(f"\nOK — authorised {account}")
    print(f"     written to {out} ({stat.S_IMODE(out.stat().st_mode):o})")
    print("\nUse it with:\n")
    print(f'  SEAMAIL_GOOGLE_CREDENTIALS="$(cat {out})" seamail search \'newer_than:7d\'')
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
