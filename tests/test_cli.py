from __future__ import annotations

from pathlib import Path

from agent_librarian_m365_snapshot_adapter.cli import main


def test_cli_invalid_config_returns_nonzero(tmp_path: Path, capsys) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{}", encoding="utf-8")
    assert main(["check-config", str(path)]) != 0
    assert "error:" in capsys.readouterr().err


def test_cli_live_export_fails_closed(capsys) -> None:
    assert main(["export"]) != 0
    assert "not implemented" in capsys.readouterr().err


def test_cli_synthetic_export(config, tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    output = tmp_path / "snapshot"
    code = main(
        [
            "export-synthetic",
            "--config",
            str(repository_root / "examples/approved-scope.example.json"),
            "--out",
            str(output),
        ]
    )
    assert code == 0
    assert (output / "source-manifest.json").is_file()
