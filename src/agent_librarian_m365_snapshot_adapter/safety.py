from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any


DEFAULT_ALLOWED_EXTENSIONS = frozenset({".md", ".json", ".yaml", ".yml"})
_FORBIDDEN_FIELD = re.compile(
    r"(?:^|_)(?:access_?token|refresh_?token|client_?secret|password|api_?key|credential)(?:$|_)",
    re.IGNORECASE,
)
_FORBIDDEN_PUBLIC_MARKERS = (
    ("live URL", re.compile(r"https?://", re.IGNORECASE)),
    ("SharePoint host", re.compile(r"sharepoint\.com", re.IGNORECASE)),
    ("password marker", re.compile(r"\bpassword\b", re.IGNORECASE)),
    ("secret marker", re.compile(r"\bsecret\b", re.IGNORECASE)),
    ("token marker", re.compile(r"\btoken\b", re.IGNORECASE)),
    ("API key marker", re.compile(r"\bapi_key\b", re.IGNORECASE)),
    ("credential marker", re.compile(r"\bcredentials?\b", re.IGNORECASE)),
    ("environment file marker", re.compile(r"(?:^|[/\\\s])\.env(?:$|[/\\\s])", re.IGNORECASE)),
)
_BROAD_SCOPE_PARTS = {"*", "**", "/", ".", "root", "all", "shared documents"}


class SafetyError(ValueError):
    """Raised when input violates a fail-closed safety boundary."""


def safe_relative_path(value: str, *, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value.strip():
        raise SafetyError(f"{label} must be a non-empty relative path")
    if "\\" in value:
        raise SafetyError(f"{label} must use forward slashes")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise SafetyError(f"{label} must be a relative path inside the approved scope")
    if ":" in path.parts[0]:
        raise SafetyError(f"{label} must not be a drive-qualified path")
    return path


def validate_included_root(value: str) -> PurePosixPath:
    path = safe_relative_path(value, label="approved_scope.included_roots entry")
    normalized = path.as_posix().casefold()
    if normalized in _BROAD_SCOPE_PARTS or len(path.parts) < 2:
        raise SafetyError(
            "approved scope is broad or ambiguous; include an explicit library/folder path"
        )
    if any(part.casefold() in {"*", "**"} for part in path.parts):
        raise SafetyError("approved scope must not contain wildcards")
    return path


def ensure_within(path: PurePosixPath, root: PurePosixPath) -> bool:
    path_parts = tuple(part.casefold() for part in path.parts)
    root_parts = tuple(part.casefold() for part in root.parts)
    return path_parts[: len(root_parts)] == root_parts


def resolve_fixture_content(content_root: Path, value: str) -> Path:
    relative = safe_relative_path(value, label="fixture content path")
    root = content_root.resolve()
    candidate = root.joinpath(*relative.parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SafetyError("fixture content path escapes the fixture directory") from exc
    if not candidate.is_file():
        raise SafetyError(f"fixture content file does not exist: {relative.as_posix()}")
    return candidate


def reject_sensitive_fields(value: Any, *, location: str = "fixture") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if _FORBIDDEN_FIELD.search(str(key)):
                raise SafetyError(f"{location} contains prohibited sensitive field {key!r}")
            reject_sensitive_fields(child, location=f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_sensitive_fields(child, location=f"{location}[{index}]")


def reject_public_markers(value: str | bytes, *, location: str) -> None:
    if isinstance(value, bytes):
        try:
            text = value.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SafetyError(f"{location} must be UTF-8 text") from exc
    else:
        text = value
    for label, pattern in _FORBIDDEN_PUBLIC_MARKERS:
        if pattern.search(text):
            raise SafetyError(f"{location} contains prohibited {label}")
