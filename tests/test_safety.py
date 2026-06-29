from __future__ import annotations

import pytest

from agent_librarian_m365_snapshot_adapter.safety import SafetyError, reject_sensitive_fields, safe_relative_path


@pytest.mark.parametrize("value", ["../escape.md", "folder/../../escape.md", "/absolute.md", "C:/drive.md"])
def test_path_traversal_and_absolute_paths_are_rejected(value: str) -> None:
    with pytest.raises(SafetyError):
        safe_relative_path(value, label="test path")


@pytest.mark.parametrize("field", ["access_token", "refreshToken", "client_secret", "password", "api_key"])
def test_sensitive_fixture_fields_are_rejected(field: str) -> None:
    with pytest.raises(SafetyError, match="sensitive field"):
        reject_sensitive_fields({field: "fabricated-value"})
