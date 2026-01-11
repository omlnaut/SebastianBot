def build_prompt(content: str) -> str:
    prompt = f"""You are my personal assistant, managing incoming emails.
    Your goal is to decide if an email requires my attention or can be ignored.
    You have the following options:
    1. Create a task in my calendar. This should be used whenever the mail content means that I need to do something. I.e. attend an appointment, make a call, send an email, or reschedule an appointment.
        Include details in the notes, such as location or specific instructions (if applicable).
    2. Send a telegram message. This should be used if the mail content is important, but creating a task does not make sense.

    You may chose to any number and any combination of the above options, or none at all.
    Reply in german.

    ---Mail content (text only)---
    {content}
    ---End of mail content---"""

    return prompt


def clean_html_tags(html_content: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text()
    return text
