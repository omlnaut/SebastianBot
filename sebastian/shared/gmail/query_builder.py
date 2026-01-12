from datetime import datetime


class GmailQueryBuilder:
    """Helper class to build Gmail search queries"""

    def __init__(self):
        self._query_parts = []

    def has_attachment(self, filetype: str | None = None) -> "GmailQueryBuilder":
        """Add has:attachment filter, optionally filtering by file type"""
        if filetype:
            self._query_parts.append(f"has:attachment filename:{filetype}")
        else:
            self._query_parts.append("has:attachment")
        return self

    def from_email(self, email: str) -> "GmailQueryBuilder":
        """Add from: filter"""
        self._query_parts.append(f"from:{email}")
        return self

    def exclude_me(self) -> "GmailQueryBuilder":
        """Exclude emails from me (the authenticated user)"""
        self._query_parts.append("-from:me")
        return self

    def subject(self, text: str, exact: bool = True) -> "GmailQueryBuilder":
        """Add subject: filter"""
        if exact:
            self._query_parts.append(f'subject:"{text}"')
        else:
            self._query_parts.append(f"subject:{text}")
        return self

    def after_date(self, date: datetime | int) -> "GmailQueryBuilder":
        """Add after: filter using Unix timestamp"""
        if isinstance(date, datetime):
            timestamp = int(date.timestamp())
        else:
            timestamp = int(date)
        self._query_parts.append(f"after:{timestamp}")
        return self

    def build(self) -> str:
        """Build the final query string"""
        return " ".join(self._query_parts)
