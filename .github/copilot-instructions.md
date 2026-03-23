# Project structure
The project root dir is always */workspaces/SebastianBot*. Code is organized as follows:
- **cloud/** contains azure related code
    - **dependencies/** for constructing usecases, services and clients from the application layer
    - **functions/** for defining azure functions
        - **side_effects/** for functions that trigger side effects in external services
            - i.e. creating google tasks or sending telegram messages
            - in general one function per file, but might contain a second "test_..." function (http triggered for manually testing an eventgrid triggered function)
        - **infrastructure/** legacy dir. Everything in here should be moved to side_effects eventually
    - **helper/** for azure related helpers
- **sebastian/** contains core logic for the bot (application layer):
    - **clients/** for defining clients to interact with external services
    - **protocols/** for defining interfaces (Python Protocols) for clients, enabling dependency injection and testability. This will be reworked. The protocol should be defined by the entity which uses it (specific to that use case)
    - **usecases/** usecases are called by the corresponding functions from cloud/
        - **side_effects** usecases are called by the corresponding functions from cloud/
    - **infrastructure/** same as usecases, but focused on interaction with external services that are triggered by events (i.e. sending telegram messages, creating tasks in google calendar, etc). This is legacy and should eventually be moved to *usecases/side_effects/*
    - **shared/** common code used in application layer
    - **clients** and **usecases** might include "investigation.iypnb" notebooks, showcasing or testing the usage
        - always include as first cell: 
                %load_ext autoreload
                %autoreload 2

                import sys
                sys.path.append("/workspaces/SebastianBot")
- **.github/** contains instruction files (.md, also nested)
    - copilot-instructions.md: general instructions, like coding style and architecture principles
    - instructions/: specific instructions for different tasks (e.g., creating a new service)

## Guidelines
### agentic coding
- Delay asking for user input as much as possible. I.e. when creating a new client that needs a new scope in a token, ask for adding that scope after the implementation is done (not at the start)
- When creating new .py files, pylance does not pick them up for type checking automatically. Before checking for any kind of errors in the problem tab, always restart the python language server
### Project structure
- Follow clean architecture principles: separate concerns between different layers (cloud vs sebastian)
    - sebastian (application layer) should not depend on cloud (infrastructure layer)
- when naming files, use simple names (i.e. client.py instead of RedditClient.py)
- use __init__.py, but leave it empty (except explicitly instructed otherwise)

### Flow
A usecase should only contain a request model, a handler class and protocols for all external dependencies that get dependency injected. A cloud function that calls the usecase does so through the *perform_usecase* method. You pass in a mapping function from the EventGrid event to the request model, and a function to resolve the handler. The return type of a usecase handler should always be an *AllActor* object, which then gets mapped to *AllActorEventGrid* and handled accordingly.

### Code
- use type hints everywhere. if not possible because external packages don't support it, use type: ignore comments or extract calls to that library into a wrapper with standard type checking. By default, files should not have open typing problems.
- make sure classes only "expose" their public methods and attributes. use leading underscore for private methods/attributes
- public methods should orchestrate calls to private methods to clearly show the logical flow. private methods should not call other private methods
- use comprehensions and early returns/continue to write more concise code
- include relevant information, like IDs, in log messages
- represent time spans passed into methods as `timedelta` (e.g. prefer `time_back: timedelta` over `hours_back: int`). Convert to absolute timestamps within the method body.
- use | None instead of Optional[...] for none-able type hints
- in general, don't handle exceptions. Every usecase will be wrapped in caller functions with a try except, handling unexpected exceptions. Excempt are cases where certain exceptions should be handled 'locally'