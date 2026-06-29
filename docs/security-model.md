# Security model

## Boundary

This companion adapter owns provider-specific export behavior. Core
`agent-librarian` remains local-only, provider-neutral, and unaware of Microsoft
authentication. The adapter may write only a local source snapshot; every
remote operation in a future implementation must be explicitly allowlisted as
read-only.

Broad tenant discovery and crawling are prohibited. Write, update, upload,
move, rename, delete, sharing, and permission-changing operations are prohibited.
The approved scope, not an identity's maximum permission, bounds each run.

## Threats and controls

| Threat | Prototype control |
| --- | --- |
| Excessive collection | Exactly one explicit library/folder root; no wildcards; bounded depth |
| Path escape or overwrite | POSIX relative-path validation; resolved fixture containment; new output only |
| Unsupported content | `.md`, `.json`, `.yaml`, and `.yml` are the maximum allowlist |
| Sensitive auth material in output | No auth implementation; sensitive fixture field names are rejected |
| Partial or misleading snapshots | Staged export; exact byte size and SHA-256; all selected files manifested |
| Network use in tests | Synthetic exporter has no network client; tests monkeypatch sockets to fail |
| Accidental publication | local output ignored; sensitivity and inherited handling recorded in manifest |
| Error disclosure | errors report configuration fields and synthetic paths, never content or auth data |

The synthetic mode uses fabricated fixtures only. It does not prove live
connector readiness.

## Future authentication and least privilege

Any future live design requires separate approval. Microsoft currently documents
Selected permission scopes for restricting an application to specifically
granted SharePoint or OneDrive resources. The intended review starting point is
a read grant using the narrowest Selected scope that supports the approved
library/folder. Broad `Sites.Read.All` or `Files.Read.All` consent does not satisfy
this repository's scope boundary merely because it is read-only.

Use a Microsoft-supported authentication library and flow selected for the
operator scenario. Prefer certificate or managed identity material over a client
password where an unattended design is approved. Never persist auth material in
the repository, snapshot, logs, traces, or public CI. Token cache storage,
redaction, revocation, rotation, and conditional-access behavior require explicit
design and review before implementation.

Relevant official guidance:

- [Selected permissions overview](https://learn.microsoft.com/en-us/graph/permissions-selected-overview)
- [Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference)
- [List drive item children](https://learn.microsoft.com/en-us/graph/api/driveitem-list-children?view=graph-rest-1.0)
- [Get a SharePoint site](https://learn.microsoft.com/en-us/graph/api/site-get?view=graph-rest-1.0)
- [Graph authentication providers](https://learn.microsoft.com/en-us/graph/sdks/choose-authentication-providers)
- [MSAL Python token acquisition](https://learn.microsoft.com/en-us/entra/msal/python/getting-started/acquiring-tokens)

## Live security gates

Before live code is added, review and approve the exact identity type, Selected
resource grant, operation allowlist, endpoint set, pagination and retry bounds,
configuration source, auth cache handling, redaction behavior, local destination,
rollback plan, and outside-public-CI tenant test procedure. A live tenant test
must never run in public CI and must never produce a committed snapshot.
