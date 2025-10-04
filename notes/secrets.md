# Secrets

- stored as plain text in azure vault
- should be json format
- should be accessed via shared/secrets/get_secret
    - provide enum value in SecretKeys for the key name in the vault
    - pass pydantic model to parse+validate as soon as possible