from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from . import __version__
from .config import ApprovedConfig


SCHEMA_VERSION = "0.1.0"


def _notes(value: str) -> list[str]:
    return [value]


def build_manifest(
    config: ApprovedConfig,
    exported_files: list[dict[str, Any]],
    excluded_paths: list[dict[str, str]],
    *,
    exported_at: datetime | None = None,
) -> dict[str, Any]:
    timestamp = (exported_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    stamp = timestamp.isoformat().replace("+00:00", "Z")
    raw = config.raw
    scope = deepcopy(raw["approved_scope"])
    scope["allowed_extensions"] = sorted(config.allowed_extensions)
    scope["notes"] = _notes(scope["notes"])
    sensitivity = deepcopy(raw["sensitivity"])
    sensitivity["notes"] = _notes(sensitivity["notes"])
    return {
        "schema_version": SCHEMA_VERSION,
        "source_snapshot_id": f"synthetic-m365-{timestamp.strftime('%Y%m%dT%H%M%SZ')}",
        "source_system": deepcopy(raw["source_system"]),
        "approved_scope": scope,
        "local_snapshot": {
            "root_path": ".",
            "created_by": "agent-librarian-m365-snapshot-adapter",
            "catalog_ready": True,
        },
        "export": {
            "exported_at": stamp,
            "method": "synthetic-offline-fixture",
            "tool_name": "agent-librarian-m365-snapshot-adapter",
            "tool_version": __version__,
            "source_access_read_only": True,
        },
        "exported_files": sorted(exported_files, key=lambda item: item["snapshot_path"]),
        "excluded_paths": sorted(excluded_paths, key=lambda item: item["path"]),
        "sensitivity": sensitivity,
        "review": {
            "review_required": True,
            "review_owner": scope["approved_by"],
            "review_status": "example-only",
            "review_notes": [
                "Synthetic fixture output only; this does not approve or prove live connector readiness."
            ],
        },
    }
