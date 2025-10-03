from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


def get_secret(secret_name: str) -> str:
    """
    Retrieve a secret value from Azure Key Vault.

    This function connects to an Azure Key Vault using the DefaultAzureCredential
    and retrieves the value of a specified secret.

    Args:
        secret_name (str): The name of the secret to retrieve.

    Returns:
        str: The value of the secret.

    Raises:
        Exception: If the secret is not found in the Key Vault.

    Note:
        Ensure that the environment is configured with the necessary Azure credentials
        to use DefaultAzureCredential.
    """
    key_vault_url = "https://omlnaut-sebastian.vault.azure.net/"

    # Create a secret client using the DefaultAzureCredential
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

    secret_str = secret_client.get_secret(secret_name).value

    if not secret_str:
        raise Exception(f"Secret {secret_name} not found in Key Vault")

    return secret_str
