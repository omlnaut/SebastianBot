# Project structure
- root dir is always /workspaces/SebastianBot
- cloud/ contains azure related code:
    - dependencies/ for constructing usecases, services and clients from the application layer
    - functions/ for defining azure functions
        - side_effects/ for functions that trigger side effects in external services
            - i.e. creating google tasks or sending telegram messages
            - triggered via eventgrid
            - use shared/perform_usecase for general flow
            - in general one function per file, but might contain a second "test_..." function (http triggered for manually testing an eventgrid triggered function)

        - infrastructure/ legacy dir. Everything in here should be moved to side_effects eventually
    - helper/ for azure related helpers
    ##############
- sebastian/ contains core logic for the bot (application layer):
    - clients/ for defining clients to interact with external services
    - protocols/ for defining interfaces (Python Protocols) for clients, enabling dependency injection and testability
    - usecases/ for defining use cases, usually defined as services that orchestrate clients + some logic
    - infrastructure/ same as usecases, but focused on interaction with external services that are triggered by events (i.e. sending telegram messages, creating tasks in google calendar, etc)
    - shared/ common code used in application layer
    - clients and usecases might include "investigation.iypnb" notebooks, showcasing or testing the usage
        - always include as first cell: 
                %load_ext autoreload
                %autoreload 2

                import sys
                sys.path.append("/workspaces/SebastianBot")
- .github/ contains instruction files (.md, also nested)
    - copilot-instructions.md: general instructions, like coding style and architecture principles
    - instructions/: specific instructions for different tasks (e.g., creating a new service)

## General guidelines
- Follow clean architecture principles: separate concerns between different layers (cloud vs sebastian)
    - sebastian (application layer) should not depend on cloud (infrastructure layer)
- when naming files, use simple names (i.e. client.py instead of RedditClient.py)
- use __init__.py, but leave it empty (except explicitly instructed otherwise)
- use type hints everywhere. if not possible because external packages don't support it, use type: ignore comments
- make sure classes only "expose" their public methods and attributes. use leading underscore for private methods/attributes
- public methods should orchestrate calls to private methods to clearly show the logical flow. private methods should not call other private methods
- use list comprehensions and early returns/continue to write more concise code
- include relevant information, like IDs, in log messages
- represent time spans passed into methods as `timedelta` (e.g. prefer `time_back: timedelta` over `hours_back: int`). Convert to absolute timestamps within the method body.

## Error Handling Architecture
- **Service Layer (sebastian/usecases/)**: 
    - wrap try/except around client calls and external operations that may fail
    - convert exceptions to `SendMessage` objects and include in `AllActor.send_messages` list
    - keep try/except blocks narrow - around specific operations, not entire methods
    - return `AllActor` type with both successes (`create_tasks`) and errors (`send_messages`)
- **Client Layer (sebastian/clients/)**: 
    - still return `Result[T]` for explicit error handling
    - services calling clients often wrap in try/except and convert to `AllActor.send_messages`
- **Function Layer (cloud/functions/)**: 
    - no try/except needed - thin wrappers around service calls
    - errors are already captured in `AllActor.send_messages` by services
    - simply convert and output: `AllActorEventGrid.from_application(actor_result).to_output()`