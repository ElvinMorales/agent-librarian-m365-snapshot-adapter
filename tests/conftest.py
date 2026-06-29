from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_librarian_m365_snapshot_adapter.config import ApprovedConfig, load_config


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_CONFIG = REPOSITORY_ROOT / "examples" / "approved-scope.example.json"


@pytest.fixture
def config() -> ApprovedConfig:
    return load_config(EXAMPLE_CONFIG)


@pytest.fixture
def config_data() -> dict:
    return json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8"))
