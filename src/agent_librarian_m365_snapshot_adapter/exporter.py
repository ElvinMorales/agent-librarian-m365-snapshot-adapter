from __future__ import annotations

import hashlib
import json
import mimetypes
import shutil
import tempfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from .config import ApprovedConfig
from .manifest import build_manifest
from .safety import (
    SafetyError,
    ensure_within,
    reject_public_markers,
    reject_sensitive_fields,
    resolve_fixture_content,
    safe_relative_path,
)


class ExportError(ValueError):
    """Raised when a synthetic export cannot safely complete."""


def _load_fixture(index_path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExportError(f"could not read synthetic fixture index: {exc}") from exc
    reject_sensitive_fields(payload)
    if not isinstance(payload, dict) or not isinstance(payload.get("value"), list):
        raise ExportError("synthetic fixture index must contain a value array")
    if any(not isinstance(item, dict) for item in payload["value"]):
        raise ExportError("synthetic fixture entries must be objects")
    return payload["value"]


def _depth_below(path: PurePosixPath, root: PurePosixPath) -> int:
    return len(path.parts) - len(root.parts) - 1


def _matches_exclusion(
    path: PurePosixPath, approved_root: PurePosixPath, excluded: PurePosixPath
) -> bool:
    if ensure_within(path, excluded):
        return True
    relative_parts = path.parts[len(approved_root.parts) :]
    excluded_parts = tuple(part.casefold() for part in excluded.parts)
    candidate = tuple(part.casefold() for part in relative_parts)
    return candidate[: len(excluded_parts)] == excluded_parts


def export_synthetic(
    config: ApprovedConfig,
    output_dir: Path,
    *,
    fixture_index: Path | None = None,
    fixture_content_root: Path | None = None,
    exported_at: datetime | None = None,
) -> dict[str, Any]:
    fixture_root = Path(__file__).parent / "synthetic_fixtures" / "graph"
    index = fixture_index or fixture_root / "synthetic-drive-children.json"
    content_root = fixture_content_root or fixture_root / "synthetic-file-content"
    entries = _load_fixture(index)
    root = config.included_roots[0]
    plans: list[tuple[PurePosixPath, Path, dict[str, Any]]] = []
    excluded: list[dict[str, str]] = []
    selected_paths: set[str] = set()

    for entry in entries:
        source_value = entry.get("sourcePath")
        content_value = entry.get("syntheticContentPath")
        if not isinstance(source_value, str) or not isinstance(content_value, str):
            raise ExportError("each synthetic file requires sourcePath and syntheticContentPath")
        try:
            source_path = safe_relative_path(source_value, label="fixture sourcePath")
            reject_public_markers(source_value, location="fixture sourcePath")
        except SafetyError as exc:
            raise ExportError(str(exc)) from exc
        if not ensure_within(source_path, root):
            raise ExportError(f"fixture path is outside approved scope: {source_path.as_posix()}")
        relative = PurePosixPath(*source_path.parts[len(root.parts) :])
        if not relative.parts:
            raise ExportError("fixture entry must identify a file below the approved root")
        if _depth_below(source_path, root) > config.max_depth:
            excluded.append({"path": source_path.as_posix(), "reason": "exceeds approved max_depth"})
            continue
        if any(
            _matches_exclusion(source_path, root, excluded_root)
            for excluded_root in config.excluded_roots
        ):
            excluded.append({"path": source_path.as_posix(), "reason": "matches an excluded root"})
            continue
        if source_path.suffix.casefold() not in config.allowed_extensions:
            excluded.append({"path": source_path.as_posix(), "reason": "extension is not allowlisted"})
            continue
        try:
            content_path = resolve_fixture_content(content_root, content_value)
        except SafetyError as exc:
            raise ExportError(str(exc)) from exc
        if source_path.as_posix() in selected_paths:
            raise ExportError(f"duplicate fixture path: {source_path.as_posix()}")
        selected_paths.add(source_path.as_posix())
        plans.append((source_path, content_path, entry))

    if not plans:
        raise ExportError("synthetic export selected no allowlisted files")
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise ExportError(f"output directory already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=".m365-snapshot-", dir=output_dir.parent) as temp_name:
        staging = Path(temp_name) / "snapshot"
        files_root = staging / "files"
        files_root.mkdir(parents=True)
        metadata: list[dict[str, Any]] = []
        for source_path, content_path, entry in plans:
            snapshot_path = source_path.as_posix()
            destination = files_root.joinpath(*source_path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            content = content_path.read_bytes()
            try:
                reject_public_markers(content, location=f"fixture content for {snapshot_path}")
            except SafetyError as exc:
                raise ExportError(str(exc)) from exc
            destination.write_bytes(content)
            modified = entry.get("lastModifiedDateTime")
            if not isinstance(modified, str) or not modified:
                raise ExportError(f"fixture timestamp is missing for {snapshot_path}")
            try:
                parsed_modified = datetime.fromisoformat(modified.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ExportError(f"fixture timestamp is invalid for {snapshot_path}") from exc
            if parsed_modified.tzinfo is None:
                raise ExportError(f"fixture timestamp must include a timezone for {snapshot_path}")
            media_type = entry.get("file", {}).get("mimeType") if isinstance(entry.get("file"), dict) else None
            metadata.append(
                {
                    "snapshot_path": snapshot_path,
                    "source_path": source_path.as_posix(),
                    "media_type": media_type or mimetypes.guess_type(snapshot_path)[0] or "application/octet-stream",
                    "size_bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "last_modified_at": modified,
                    "classification": config.raw["sensitivity"]["level"],
                    "notes": ["Exported from fabricated Microsoft Graph-like fixture data."],
                }
            )
        manifest = build_manifest(config, metadata, excluded, exported_at=exported_at)
        (staging / "source-manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        staging.replace(output_dir)
    return manifest
