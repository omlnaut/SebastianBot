# When creating a new client, follow these instructions:
- put into clients dir, each client own folder
- data that is read from an external source should always be parsed into a pydantic basemodel
- the public interface of the client should only be built-in types or types from the domain (prefer domain esp. for return types instead of i.e. dicts)
- create a resolver in cloud/dependencies/clients.py
- use dependency injection for things like credentials (usually fetched via pydantic model from azure key vault)
- when creating client from an investigation, add cells showing the usage of the client
- check if it makes sense to extract private helper methods to make public methods more readable
- if a public method uses private helper methods, extract those helpers to a separate file named after the public method
    - name the file after the public method
    - create a `client` dir that contains the `client.py` and the helper files
        - "export" the client in the `__init__.py` of the main client dir, so no import adjustments should be needed elsewhere
        - `client.py` should use relative imports to import the helpers
        - "main" method in the helper file should contain barely any logic, just call other private methods in the helper file to improve readability
    - keeps the main client file clean and readable
    - example: `GoogleTaskClient.create_task_with_notes()` uses helpers extracted to `create_task_with_notes.py`
    - bad example: private methods that are (or could be) used by multiple public methods should stay in the main client file. i.e. authentication, token fetching, etc.

## Google clients
For clients that need authentication against google one might need to add scopes to the stored google auth token. Edit the scopes in /workspaces/SebastianBot/investigations/google_token/create_credentials.py, then prompt the user to run this file and update the token stored in the vault.

The google api library does not provide type hints. To keep this project as clean as possible, extract calls to that lib into a 'ServiceWrapper' which sets type checking to standard (instead of the global strict). See `/workspaces/SebastianBot/sebastian/clients/google/task/client/client.py` and `/workspaces/SebastianBot/sebastian/clients/google/task/client/service_wrapper.py` for example implementation.