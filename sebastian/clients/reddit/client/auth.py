import logging

import requests

from sebastian.clients.reddit.credentials import RedditCredentials


def fetch_access_token(credentials: RedditCredentials, token_url: str) -> str:
    """Get access token for Reddit API using client credentials."""
    logging.info("Fetching Reddit access token")
    headers = {
        "User-Agent": credentials.user_agent,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "password",
        "username": credentials.username,
        "password": credentials.password,
    }
    # todo: parse with pydantic
    response = requests.post(
        token_url,
        headers=headers,
        data=data,
        auth=(credentials.client_id, credentials.client_secret),
    )
    response.raise_for_status()
    token_data = response.json()
    return token_data["access_token"]
