# When creating a new client, follow these instructions:
- put into clients dir, each client own folder
- data that is read from an external source should always be parsed into a pydantic basemodel
    - extract models in a models.py
- create a resolver in cloud/dependencies/clients.py
- when creating client from an investigation, add cells showing the usage of the client