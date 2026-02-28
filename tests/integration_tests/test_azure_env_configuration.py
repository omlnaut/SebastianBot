"""
Integration test to verify Azure Function App environment variables are properly configured.

This test runs locally and queries the Azure Function App configuration to verify
that COMPLETETASK EventGrid environment variables are set in the cloud environment.

Requires:
- Azure CLI authentication (run 'az login') OR DefaultAzureCredential setup
- Environment variables: AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AZURE_FUNCTION_APP_NAME
"""

import os
import pytest
from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient
from pydantic import ValidationError

from cloud.functions.side_effects.complete_task.models import CompleteTaskEventGrid
from cloud.helper.event_grid import EventGridInfo


@pytest.fixture(scope="module")
def azure_function_app_settings() -> dict[str, str]:
    """Fetch application settings from Azure Function App."""
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    resource_group = os.environ.get("AZURE_RESOURCE_GROUP")
    function_app_name = os.environ.get("AZURE_FUNCTION_APP_NAME")

    assert subscription_id and resource_group and function_app_name is not None

    # Authenticate using DefaultAzureCredential (supports Azure CLI, Managed Identity, etc.)
    credential = DefaultAzureCredential()
    client = WebSiteManagementClient(credential, subscription_id)

    # Fetch application settings from Azure
    app_settings = client.web_apps.list_application_settings(
        resource_group_name=resource_group, name=function_app_name
    )

    assert app_settings is not None
    assert app_settings.properties is not None

    return app_settings.properties


# todo: continue here
def test_completetask_eventgrid_info_structure(
    azure_function_app_settings: dict[str, str],
):
    """EventGrid configuration should exist and follow EventGridInfo structure."""
    env_var_name = CompleteTaskEventGrid.env_name()

    env_value = azure_function_app_settings.get(env_var_name)
    assert env_value is not None, (
        f"{env_var_name} not set in Azure Function App. "
        f"Add this environment variable with EventGrid configuration (JSON, see EventGridInfo)."
    )

    # Validate it follows EventGridInfo structure
    try:
        EventGridInfo.model_validate_json(env_value)
    except ValidationError as e:
        pytest.fail(f"EventGridInfo validation failed: {e}")