# Synthetic demo

Install and run entirely offline:

```bash
python -m pip install -e ".[dev]"
m365-snapshot-adapter check-config examples/approved-scope.example.json
m365-snapshot-adapter export-synthetic --config examples/approved-scope.example.json --out .tmp/synthetic-snapshot
```

The output contains:

```text
.tmp/synthetic-snapshot/
  source-manifest.json
  files/
    Shared Documents/
      Synthetic Team Space/
        policy-note.md
        Guides/
          prompt-note.md
```

The fabricated `.txt` fixture is recorded as excluded because it is not
allowlisted. The manifest records approved scope, sensitivity, review status,
read-only method, source and snapshot paths, media type, byte size, SHA-256, and
fixture modification timestamp.

Tests and the demo use local fixtures only. They make no live Graph call, require
no Microsoft SDK, and use no tenant or auth configuration. A successful demo
does not prove live connector readiness. Any live tenant test must remain outside
public CI, and real snapshots and derived catalogs must never be committed.
