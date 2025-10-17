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
- topics are independet of resource groups
- subscriptions are what ties the activation to a certain resource
- for now, re-use the existing topics to slowly migrate to the new project
