from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from .safety import (
    DEFAULT_ALLOWED_EXTENSIONS,
    SafetyError,
    reject_sensitive_fields,
    safe_relative_path,
    validate_included_root,
)


class ConfigError(ValueError):
    """Raised when approved-scope configuration is invalid."""


@dataclass(frozen=True)
class ApprovedConfig:
    raw: dict[str, Any]
    included_roots: tuple[PurePosixPath, ...]
    excluded_roots: tuple[PurePosixPath, ...]
    allowed_extensions: frozenset[str]
    max_depth: int


def _reject_unknown(parent: dict[str, Any], allowed: set[str], prefix: str) -> None:
    unknown = sorted(set(parent) - allowed)
    if unknown:
        raise ConfigError(f"{prefix} contains unsupported field(s): {', '.join(unknown)}")


def _object(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"{key} is required and must be an object")
    return value


def _text(parent: dict[str, Any], key: str, prefix: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{prefix}.{key} is required and must be non-empty")
    return value


def _text_list(parent: dict[str, Any], key: str, prefix: str, *, nonempty: bool) -> list[str]:
    value = parent.get(key)
    if not isinstance(value, list) or (nonempty and not value):
        qualifier = "a non-empty" if nonempty else "an"
        raise ConfigError(f"{prefix}.{key} must be {qualifier} array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ConfigError(f"{prefix}.{key} entries must be non-empty strings")
    if len(value) != len(set(value)):
        raise ConfigError(f"{prefix}.{key} entries must be unique")
    return value


def _parse_datetime(value: str, field: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ConfigError(f"{field} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ConfigError(f"{field} must include a timezone")


def validate_config(data: Any) -> ApprovedConfig:
    if not isinstance(data, dict):
        raise ConfigError("configuration must be a JSON object")
    try:
        reject_sensitive_fields(data, location="configuration")
    except SafetyError as exc:
        raise ConfigError(str(exc)) from exc
    _reject_unknown(data, {"source_system", "approved_scope", "sensitivity"}, "configuration")
    source = _object(data, "source_system")
    _reject_unknown(
        source,
        {"type", "name", "provider_hint", "source_locator"},
        "source_system",
    )
    for key in ("type", "name", "provider_hint", "source_locator"):
        _text(source, key, "source_system")
    if source["type"] != "microsoft-365-sharepoint":
        raise ConfigError("source_system.type must be 'microsoft-365-sharepoint'")

    scope = _object(data, "approved_scope")
    _reject_unknown(
        scope,
        {
            "description",
            "approved_by",
            "approved_at",
            "included_roots",
            "excluded_roots",
            "allowed_extensions",
            "max_depth",
            "notes",
        },
        "approved_scope",
    )
    for key in ("description", "approved_by", "approved_at"):
        _text(scope, key, "approved_scope")
    _parse_datetime(scope["approved_at"], "approved_scope.approved_at")
    included_values = _text_list(scope, "included_roots", "approved_scope", nonempty=True)
    excluded_values = _text_list(scope, "excluded_roots", "approved_scope", nonempty=False)
    allowed_values = _text_list(scope, "allowed_extensions", "approved_scope", nonempty=True)
    included = tuple(validate_included_root(value) for value in included_values)
    if len(included) != 1:
        raise ConfigError("prototype requires exactly one explicit included root")
    excluded = tuple(
        safe_relative_path(value, label="approved_scope.excluded_roots entry")
        for value in excluded_values
    )
    allowed = frozenset(value.casefold() for value in allowed_values)
    if any(not value.startswith(".") or "/" in value or "\\" in value for value in allowed):
        raise ConfigError("allowed extensions must be simple dot-prefixed extensions")
    unsupported = sorted(allowed - DEFAULT_ALLOWED_EXTENSIONS)
    if unsupported:
        raise ConfigError(f"unsupported allowed extension(s): {', '.join(unsupported)}")
    max_depth = scope.get("max_depth")
    if not isinstance(max_depth, int) or isinstance(max_depth, bool) or max_depth < 0:
        raise ConfigError("approved_scope.max_depth must be a non-negative integer")
    _text(scope, "notes", "approved_scope")

    sensitivity = _object(data, "sensitivity")
    _reject_unknown(
        sensitivity,
        {
            "level",
            "generated_outputs_inherit_sensitivity",
            "may_commit_snapshot",
            "may_commit_generated_outputs",
            "notes",
        },
        "sensitivity",
    )
    level = _text(sensitivity, "level", "sensitivity")
    if level not in {"public-synthetic", "public", "internal", "private-local", "restricted"}:
        raise ConfigError("sensitivity.level is not supported by source manifest schema 0.1.0")
    if sensitivity.get("generated_outputs_inherit_sensitivity") is not True:
        raise ConfigError("generated outputs must inherit source sensitivity")
    for key in ("may_commit_snapshot", "may_commit_generated_outputs"):
        if not isinstance(sensitivity.get(key), bool):
            raise ConfigError(f"sensitivity.{key} must be boolean")
    _text(sensitivity, "notes", "sensitivity")
    return ApprovedConfig(data, included, excluded, allowed, max_depth)


def load_config(path: Path) -> ApprovedConfig:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"could not read config: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON at line {exc.lineno}, column {exc.colno}") from exc
    try:
        return validate_config(data)
    except SafetyError as exc:
        raise ConfigError(str(exc)) from exc
