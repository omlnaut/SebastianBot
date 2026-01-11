from sebastian.protocols.gmail import FullMailResponse, MessageId
from .retry_decorator import retry_on_network_error


@retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
def fetch_message_ids(service, query: str) -> list[MessageId]:
    """Fetch message IDs matching the query"""
    response = service.users().messages().list(userId="me", q=query).execute()
    messages = response.get("messages", [])
    return [MessageId.from_response(msg) for msg in messages]


@retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
def fetch_full_mail(service, msg_id: str) -> FullMailResponse:
    """Fetch full email message by ID"""
    message = (
        service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    )
    return FullMailResponse.from_response(message)
