# Microsoft 365 Snapshot Adapter for Agent Librarian

This repository is the provider-specific companion adapter for
[`agent-librarian`](https://github.com/ElvinMorales/agent-librarian). It is for
operators who need to turn a narrowly approved Microsoft 365 / SharePoint folder
scope into a local source snapshot before using the provider-neutral core CLI.
It is not the core `agent-librarian` package; the core remains local-first and
provider-neutral.

The repository exists to keep authentication, authorization, Microsoft Graph
behavior, and provider dependencies outside the local-first core package. The
only integration boundary is a local snapshot containing `source-manifest.json`
and a `files/` tree compatible with the core source snapshot contract.

The current implementation is synthetic and offline only. Public examples are
fabricated, and the live `export` command fails closed. No live connector,
Microsoft Graph access, OAuth/MSAL flow, provider SDK, tenant discovery, or
network behavior is implemented. Generated snapshots and any derived catalogs,
reports, or presentations inherit the sensitivity of their source.

## Current status

Implemented now:

- strict validation of an explicit approved folder scope
- a deterministic, offline export from fabricated Graph-like fixtures
- extension allowlisting, traversal rejection, depth bounds, and exclusions
- source manifest schema `0.1.0` metadata, including SHA-256 and byte size
- a live command that fails closed
- offline tests with no Microsoft client or network access

Intentionally not implemented:

- Microsoft Graph calls or tenant discovery
- OAuth, MSAL, credentials, persistent auth caches, or refresh behavior
- live site, drive, folder, or file access
- write, move, delete, upload, rename, sharing, or permission operations

The synthetic demo proves only the local output shape. It does not prove that a
live connector is ready, authorized, least-privileged, or safe for production.

## What to use now

Use `check-config` and `export-synthetic` to validate the local snapshot shape
and safety boundaries. The live `export` command is intentionally fail-closed
until separate [live-export security gates](docs/live-export-security-gates.md)
are designed, reviewed, and approved.

## Quickstart

```bash
python -m pip install -e ".[dev]"
m365-snapshot-adapter check-config examples/approved-scope.example.json
m365-snapshot-adapter export-synthetic --config examples/approved-scope.example.json --out .tmp/synthetic-snapshot
python -m pytest
```

The exporter refuses to replace an existing output directory. Remove or choose
a new local `.tmp/` destination before a repeat run.

Validate the output with a local checkout of the core repository:

```bash
python ../agent-librarian/scripts/check_source_snapshot.py .tmp/synthetic-snapshot
```

The core validator checks schema shape, file hashes, file sizes, manifest/file
agreement, and obvious public-example leak markers. It does not certify that an
artifact is safe to publish.

## Safety boundary

Configuration must name exactly one explicit library/folder root. Wildcards,
drive roots, traversal segments, unsupported extensions, missing approvals, and
ambiguous scope fail before output is written. Synthetic export reads only
bundled fixtures and never constructs a Microsoft Graph client.

Public examples contain fabricated placeholders only. Never commit real tenant
or account identifiers, SharePoint URLs, document names, credentials, auth
material, logs, traces, screenshots, source exports, generated catalogs, or
employer-specific examples. Local snapshots and every derived catalog, report,
or presentation inherit the source sensitivity.

See [the security model](docs/security-model.md),
[approved-scope configuration](docs/approved-scope-config.md), and
[the synthetic demo](docs/synthetic-demo.md). Future live work is blocked by the
[live-export security gates backlog](docs/live-export-security-gates.md); that
backlog does not approve a live implementation.

## Release boundary

This adapter is optional, provider-specific, separately versioned, and not part
of the `agent-librarian` package. The core remains local-only and does not
authenticate to or crawl Microsoft 365.
