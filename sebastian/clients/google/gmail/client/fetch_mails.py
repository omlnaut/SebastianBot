from sebastian.protocols.gmail import FullMailResponse, MessageId


def fetch_message_ids(service, query: str) -> list[MessageId]:
    """Fetch message IDs matching the query"""
    response = service.users().messages().list(userId="me", q=query).execute()
    messages = response.get("messages", [])
    return [MessageId.from_response(msg) for msg in messages]


def fetch_full_mail(service, msg_id: str) -> FullMailResponse:
    """Fetch full email message by ID"""
    message = (
        service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    )
    return FullMailResponse.from_response(message)
