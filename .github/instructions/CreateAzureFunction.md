# Create azure function
## General steps:
- create new folder for either:
    - usecase -> folder in /workspaces/SebastianBot/usecases
    - infrastucture -> folder in /workspaces/SebastianBot/infrastructure
- create <UseCaseName>Function.py, containing the azure function definition
- add import to /workspaces/SebastianBot/function_app.py

## Timer based function
- look at /workspaces/SebastianBot/usecases/manga/manga_update for example implementation
    - use telegram output binding for exception handling
    - if necessary, extract model classes
    - azure function shoul

## For all functions
    - if necessary, extract model classes
    - azure function should only contain validation and output mapping, logic should be in service class