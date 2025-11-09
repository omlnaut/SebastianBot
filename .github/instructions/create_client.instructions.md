# When creating a new client, follow these instructions:
- put into clients dir, each client own folder
- incoming data should always be parsed into a pydantic basemodel
    - extract models in a models.py
- create a resolver in cloud/dependencies/clients.py