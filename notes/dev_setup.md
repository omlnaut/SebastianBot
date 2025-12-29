# Development setup

## initial setup
- copy devcontainer+dockerfile from previous project
    - make sure docker python version matches function app python version
- create function app in azure web ui
    - Networking -> Enable public Access
    - Authentication -> Managed identity
- create function
    - F1 -> Azure functions: create function
    - remove venv (because using devcontainer anyway)
    - remove pip install section in tasks.json
    - Azure plugin: login to tenant (login via github)
    - manually start blob service
    - start debugging to start function, verify execution
    - azure plugin -> workspace -> deploy to azure
        - select correct function app

## secrets
- by default, permission is missing from managed identity to access secrets
- Azure portal
    - vault -> Access (IAM)
    - Add role -> Secrets Officer (read+write) or KeyVaultReader (only read)
### Access in deployment
    - needs system assigned identity
        - function App -> Identity -> enable system assigned

## event grid
1. Create new topic in azure web ui
2. Consumer:
    - create function
        - `@app.event_grid_trigger(arg_name="azeventgrid")` as decorator for function
        - `azeventgrid: func.EventGridEvent` as argument in function
        - `event = parse_payload(azeventgrid, ModelClass)` inside for parsing
    - deploy to azure

