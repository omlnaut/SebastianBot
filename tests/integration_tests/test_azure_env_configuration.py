"""
Integration test to verify Azure Function App environment variables are properly configured.

This test runs locally and queries the Azure Function App configuration to verify
that COMPLETETASK EventGrid environment variables are set in the cloud environment.

Requires:
- Azure CLI authentication (run 'az login') OR DefaultAzureCredential setup
- Environment variables: AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AZURE_FUNCTION_APP_NAME
"""

import os
from pathlib import Path
import astroid
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


from cloud.helper.event_grid import EventGridModel
import importlib


def extract_event_grid_models() -> list[str]:
    base_path = Path("/workspaces/SebastianBot/cloud/functions")
    base_name = EventGridModel.__name__
    class_names = []

    def extract_inherited_classnames(
        node: astroid.nodes.ClassDef, base_name: str
    ) -> str | None:
        base_names = [b.name for b in node.bases]
        if base_name in base_names:
            return node.name
        return None

    for file in base_path.rglob("*.py"):
        module = astroid.parse(file.read_text())
        for node in module.body:
            if not isinstance(node, astroid.nodes.ClassDef):
                continue

            if not (name := extract_inherited_classnames(node, base_name)):
                continue

            # Convert file path to module path
            relative_path = file.relative_to(Path("/workspaces/SebastianBot"))
            module_path = str(relative_path.with_suffix("")).replace("/", ".")

            # Dynamically import the module and get the class
            imported_module = importlib.import_module(module_path)
            class_type = getattr(imported_module, name)
            class_names.append(class_type.env_name())

    return class_names


@pytest.mark.parametrize("env_var_name", extract_event_grid_models())
def test_eventgrid_info_structure(
    azure_function_app_settings: dict[str, str],
    env_var_name: str,
):
    """EventGrid configuration should exist and follow EventGridInfo structure."""
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
