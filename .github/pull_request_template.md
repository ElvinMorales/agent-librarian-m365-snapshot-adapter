## Summary

## Safety / boundaries

- [ ] No live Microsoft Graph access added.
- [ ] No OAuth/MSAL implementation added.
- [ ] No provider SDK dependency added.
- [ ] No tenant discovery added.
- [ ] No live network behavior added.
- [ ] No credentials, tokens, tenant IDs, real SharePoint URLs, screenshots, private exports, or employer-specific examples added.
- [ ] Public examples remain synthetic.
- [ ] Live `export` remains fail-closed unless this PR is explicitly approved live-export work.

## Validation

- [ ] `python -m pytest`
- [ ] `m365-snapshot-adapter check-config examples/approved-scope.example.json`
- [ ] `m365-snapshot-adapter export-synthetic --config examples/approved-scope.example.json --out .tmp/synthetic-snapshot`
- [ ] `m365-snapshot-adapter export --config examples/approved-scope.example.json --out .tmp/live-should-fail` fails closed
- [ ] `git diff --check`
