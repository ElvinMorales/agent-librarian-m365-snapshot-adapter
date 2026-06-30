# Live Export Security Gates

Status: Backlog. No live export implementation is approved by this document.

## Purpose

This document lists the gates that must be designed, reviewed, and approved
before the adapter may add live Microsoft Graph / Microsoft 365 export behavior.

The current adapter remains synthetic/offline. The live `export` command must
remain fail-closed until these gates are satisfied by a separate reviewed change.

## Non-goals

- no live implementation in the repo hygiene issue
- no OAuth/MSAL implementation in the repo hygiene issue
- no tenant discovery
- no broad crawling
- no public CI tenant tests
- no committed private snapshots
- no committed raw provider responses
- no committed auth logs, traces, screenshots, or private exports

## Required gates before live code

- identity type and authentication flow selected
- least-privilege resource grant documented
- explicit approved site/library/folder scope
- endpoint allowlist
- operation allowlist limited to read-only file metadata and content reads
- pagination and retry bounds
- rate-limit behavior
- file extension allowlist
- maximum depth and file count limits
- path containment rules
- destination handling and no-overwrite behavior
- redaction policy for errors and logs
- token/cache storage policy
- local config storage policy
- rollback/abort behavior
- private tenant test procedure outside public CI
- evidence that emitted snapshot passes core source snapshot conformance

## Public boundary

Live tenant tests, real configs, raw provider responses, auth logs, screenshots,
source exports, generated catalogs from private snapshots, and private source
snapshots must never be committed.

## Relationship to core agent-librarian

The live adapter, if approved later, must emit a local snapshot containing
`source-manifest.json` and a `files/` tree compatible with the core
`agent-librarian` source snapshot contract. The core package must remain
local-first and provider-neutral.
