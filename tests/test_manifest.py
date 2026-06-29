from __future__ import annotations

import json
from pathlib import Path

from jsonschema import FormatChecker
from jsonschema.validators import validator_for

from agent_librarian_m365_snapshot_adapter.exporter import export_synthetic


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_generated_manifest_matches_vendored_core_schema(config, tmp_path: Path) -> None:
    output = tmp_path / "snapshot"
    export_synthetic(config, output)
    manifest = json.loads((output / "source-manifest.json").read_text(encoding="utf-8"))
    schema = json.loads(
        (REPOSITORY_ROOT / "schemas/source-manifest.schema.json").read_text(encoding="utf-8")
    )
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    validator_class(schema, format_checker=FormatChecker()).validate(manifest)
    assert manifest["schema_version"] == "0.1.0"
    assert manifest["export"]["source_access_read_only"] is True
    assert manifest["sensitivity"]["generated_outputs_inherit_sensitivity"] is True


def test_manifest_contains_no_auth_material(config, tmp_path: Path) -> None:
    output = tmp_path / "snapshot"
    export_synthetic(config, output)
    text = (output / "source-manifest.json").read_text(encoding="utf-8").casefold()
    for prohibited in ("access_token", "refresh_token", "client_secret", "api_key", "password"):
        assert prohibited not in text
