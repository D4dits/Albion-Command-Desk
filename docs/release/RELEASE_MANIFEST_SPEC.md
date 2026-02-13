# Release Manifest Specification (v1)

This document defines the update metadata contract used by:
- installer/bootstrap scripts,
- in-app update checks.

The manifest is JSON and must be UTF-8 encoded.

## Canonical filename

- `manifest.json`

## Top-level schema

```json
{
  "schema_version": 1,
  "app_id": "albion-command-desk",
  "channel": "stable",
  "published_at": "2026-02-13T12:00:00Z",
  "latest": {
    "version": "0.1.1",
    "release_url": "https://github.com/D4dits/Albion-Command-Desk/releases/tag/v0.1.1",
    "changelog_url": "https://github.com/D4dits/Albion-Command-Desk/blob/main/CHANGELOG.md",
    "min_supported_version": "0.1.0"
  },
  "assets": [
    {
      "os": "windows",
      "arch": "x86_64",
      "kind": "installer",
      "name": "AlbionCommandDesk-Setup.exe",
      "url": "https://github.com/D4dits/Albion-Command-Desk/releases/download/v0.1.1/AlbionCommandDesk-Setup.exe",
      "sha256": "a3f0...9ab1",
      "size": 36713339
    }
  ]
}
```

## Required fields

Top-level:
- `schema_version` (integer): currently `1`.
- `app_id` (string): must be `albion-command-desk`.
- `channel` (string): one of `stable`, `beta`, `nightly`.
- `published_at` (RFC3339 UTC string).
- `latest` (object).
- `assets` (array, can be empty if only notifying version/changelog).

`latest`:
- `version` (string, semver without `v`, e.g. `0.1.1`).
- `release_url` (string, absolute HTTPS URL).
- `changelog_url` (string, absolute HTTPS URL).
- `min_supported_version` (string, semver).

`assets[]`:
- `os` (string): `windows`, `linux`, or `macos`.
- `arch` (string): `x86_64` or `arm64`.
- `kind` (string): `installer`, `archive`, or `bootstrap-script`.
- `name` (string): artifact filename.
- `url` (string, absolute HTTPS URL).
- `sha256` (string, lowercase hex digest).
- `size` (integer, bytes, > 0).

## Compatibility and behavior rules

- Unknown fields must be ignored by clients (forward compatibility).
- Missing required fields must invalidate the manifest.
- Clients must ignore assets with unknown `os`, `arch`, or `kind`.
- `latest.version` newer than local version means update available.
- If local version `< min_supported_version`, client should show hard upgrade warning.

## Versioning policy

- Breaking schema changes require incrementing `schema_version`.
- `schema_version=1` contract is immutable once released.
- New optional fields are allowed without schema bump.

## Security requirements

- Manifest and assets must be served over HTTPS.
- Clients should verify `sha256` before using downloaded artifact.
- Do not embed secrets/tokens in the manifest.

