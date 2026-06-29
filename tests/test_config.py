from __future__ import annotations

import pytest

from agent_librarian_m365_snapshot_adapter.config import ConfigError, validate_config


def test_valid_example_config_passes(config) -> None:
    assert config.included_roots[0].as_posix() == "Shared Documents/Synthetic Team Space"


def test_missing_required_scope_fails(config_data) -> None:
    del config_data["approved_scope"]
    with pytest.raises(ConfigError, match="approved_scope"):
        validate_config(config_data)


@pytest.mark.parametrize("root", ["/", "root", "all", "Shared Documents", "*/Folder"])
def test_broad_or_ambiguous_scope_fails(config_data, root: str) -> None:
    config_data["approved_scope"]["included_roots"] = [root]
    with pytest.raises((ConfigError, ValueError), match="broad|wildcard|relative"):
        validate_config(config_data)


def test_unsupported_configured_extension_fails(config_data) -> None:
    config_data["approved_scope"]["allowed_extensions"].append(".exe")
    with pytest.raises(ConfigError, match="unsupported"):
        validate_config(config_data)


def test_unknown_or_auth_shaped_config_fields_fail(config_data) -> None:
    config_data["client_secret"] = "fabricated"
    with pytest.raises(ConfigError, match="sensitive field"):
        validate_config(config_data)


def test_approval_timestamp_requires_timezone(config_data) -> None:
    config_data["approved_scope"]["approved_at"] = "2026-06-29T00:00:00"
    with pytest.raises(ConfigError, match="timezone"):
        validate_config(config_data)
