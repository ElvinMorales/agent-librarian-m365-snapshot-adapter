from __future__ import annotations

import hashlib
import json
import socket
from pathlib import Path

import pytest

from agent_librarian_m365_snapshot_adapter.exporter import ExportError, export_synthetic


def test_synthetic_export_is_offline_and_writes_only_allowlisted_files(
    config, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def network_denied(*args, **kwargs):
        raise AssertionError("synthetic export attempted network access")

    monkeypatch.setattr(socket, "socket", network_denied)
    output = tmp_path / "snapshot"
    manifest = export_synthetic(config, output)

    assert (output / "source-manifest.json").is_file()
    actual = sorted(
        path.relative_to(output / "files").as_posix()
        for path in (output / "files").rglob("*")
        if path.is_file()
    )
    assert actual == [
        "Shared Documents/Synthetic Team Space/Guides/prompt-note.md",
        "Shared Documents/Synthetic Team Space/policy-note.md",
    ]
    assert all(Path(path).suffix in config.allowed_extensions for path in actual)
    assert manifest["excluded_paths"] == [
        {
            "path": "Shared Documents/Synthetic Team Space/unsupported.txt",
            "reason": "extension is not allowlisted",
        }
    ]


def test_manifest_metadata_matches_output_files(config, tmp_path: Path) -> None:
    output = tmp_path / "snapshot"
    manifest = export_synthetic(config, output)
    for entry in manifest["exported_files"]:
        content = (output / "files" / Path(entry["snapshot_path"])).read_bytes()
        assert entry["size_bytes"] == len(content)
        assert entry["sha256"] == hashlib.sha256(content).hexdigest()
        assert entry["source_path"] == entry["snapshot_path"]
        assert entry["classification"] == "public-synthetic"
        assert entry["last_modified_at"].endswith("Z")


def test_fixture_path_traversal_aborts_without_output(config, tmp_path: Path) -> None:
    content_root = tmp_path / "content"
    content_root.mkdir()
    (content_root / "note.md").write_text("fabricated", encoding="utf-8")
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps(
            {
                "value": [
                    {
                        "sourcePath": "Shared Documents/Synthetic Team Space/../escape.md",
                        "syntheticContentPath": "note.md",
                        "lastModifiedDateTime": "2026-06-29T00:00:00Z",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "snapshot"
    with pytest.raises(ExportError, match="approved scope"):
        export_synthetic(
            config,
            output,
            fixture_index=fixture,
            fixture_content_root=content_root,
        )
    assert not output.exists()


def test_sensitive_fields_never_reach_output(config, tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text('{"access_token": "fabricated", "value": []}', encoding="utf-8")
    output = tmp_path / "snapshot"
    with pytest.raises(ValueError, match="sensitive field"):
        export_synthetic(config, output, fixture_index=fixture)
    assert not output.exists()


def test_existing_output_is_not_replaced(config, tmp_path: Path) -> None:
    output = tmp_path / "snapshot"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    with pytest.raises(ExportError, match="already exists"):
        export_synthetic(config, output)
    assert marker.read_text(encoding="utf-8") == "keep"


def test_secret_like_fixture_content_is_rejected(config, tmp_path: Path) -> None:
    content_root = tmp_path / "content"
    content_root.mkdir()
    (content_root / "note.md").write_text("access token: fabricated", encoding="utf-8")
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps(
            {
                "value": [
                    {
                        "sourcePath": "Shared Documents/Synthetic Team Space/note.md",
                        "syntheticContentPath": "note.md",
                        "lastModifiedDateTime": "2026-06-29T00:00:00Z",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "snapshot"
    with pytest.raises(ExportError, match="token marker"):
        export_synthetic(
            config,
            output,
            fixture_index=fixture,
            fixture_content_root=content_root,
        )
    assert not output.exists()
