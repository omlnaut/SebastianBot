# pyright: standard
from typing import Any

import pytest

from cloud.helper import SecretKeys, get_secret
from cloud.helper.secrets import TypedSecretKey


@pytest.mark.parametrize(
    "key",
    [value for value in vars(SecretKeys).values() if isinstance(value, TypedSecretKey)],
    ids=lambda k: k._name,
)
def test_secret_can_be_fetched_and_parsed(key: TypedSecretKey[Any]) -> None:
    result = get_secret(key)
    assert isinstance(result, key.model)
