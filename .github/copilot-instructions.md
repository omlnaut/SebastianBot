# Project structure
- root dir is always /workspaces/SebastianBot
- cloud/ contains azure related code:
    - functions/ for defining azure functions. One function per file.
    - dependencies/ for constructing services and clients from the application layer
    - helper/ for azure related helpers
- sebastian/ contains core logic for the bot (application layer):
    - clients/ for defining clients to interact with external services
    - usecases/ for defining use cases, usually defined as services that orchestrate clients + some logic
    - infrastructure/ same as usecases, but focused on interaction with external services that are triggered by events (i.e. sending telegram messages, creating tasks in google calendar, etc)
    - shared/ common code used in application layer

## General guidelines
- Follow clean architecture principles: separate concerns between different layers (cloud vs sebastian)
    - sebastian (application layer) should not depend on cloud (infrastructure layer)
- when naming files, use simple names (i.e. client.py instead of RedditClient.py)