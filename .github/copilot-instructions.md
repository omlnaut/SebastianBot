# Project structure
- root dir is always /workspaces/SebastianBot
- cloud/ contains azure related code:
    - functions/ for defining azure functions. One function per file.
        - functions might be nested into subdirectories for better organization
    - dependencies/ for constructing services and clients from the application layer
    - helper/ for azure related helpers
- sebastian/ contains core logic for the bot (application layer):
    - clients/ for defining clients to interact with external services
    - usecases/ for defining use cases, usually defined as services that orchestrate clients + some logic
    - infrastructure/ same as usecases, but focused on interaction with external services that are triggered by events (i.e. sending telegram messages, creating tasks in google calendar, etc)
    - shared/ common code used in application layer
    - clients and usecases might include "investigation.iypnb" notebooks, showcasing or testing the usage
        - always include as first cell: 
                %load_ext autoreload
                %autoreload 2

                import sys
                sys.path.append("/workspaces/SebastianBot")

## General guidelines
- Follow clean architecture principles: separate concerns between different layers (cloud vs sebastian)
    - sebastian (application layer) should not depend on cloud (infrastructure layer)
- when naming files, use simple names (i.e. client.py instead of RedditClient.py)
- use __init__.py
- use type hints everywhere. if not possible because external packages don't support it, use type: ignore comments