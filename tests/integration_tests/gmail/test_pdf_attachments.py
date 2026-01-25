from datetime import datetime, timedelta

from sebastian.protocols.gmail.IClient import IGmailClient
from sebastian.shared.gmail.query_builder import GmailQueryBuilder


def test_download_pdf_attachments(gmail_client: IGmailClient):
    today_last_year = datetime.now() - timedelta(days=365)
    query = (
        GmailQueryBuilder()
        .from_email("microsoft-noreply@microsoft.com")
        .has_attachment(filetype="pdf")
        .after_date(today_last_year)
        .build()
    )

    mails = gmail_client.fetch_mails(query)
    assert len(mails) > 0, "No emails with PDF attachments found"

    attachments = gmail_client.download_pdf_attachments(mails[0])
    assert len(attachments) > 0, "No PDF attachments downloaded"
    assert all(isinstance(attachment.data, bytes) for attachment in attachments)
