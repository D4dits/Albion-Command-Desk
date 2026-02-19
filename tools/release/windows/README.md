# Windows Release Bootstrap Builder

Builds the canonical Windows release bootstrap executable:

- output name: `AlbionCommandDesk-Setup-vX.Y.Z-x86_64.exe`
- purpose: download tagged source zip, run `tools/install/windows/install.ps1`, and keep console open on error.

## Usage

From repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\release\windows\build_bootstrap_setup.ps1 -ReleaseTag v0.1.14
```

Custom output path:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\release\windows\build_bootstrap_setup.ps1 `
  -ReleaseTag v0.1.14 `
  -OutputPath .\dist\installer\AlbionCommandDesk-Setup-v0.1.14-x86_64.exe
```

## Notes

- `ReleaseTag` accepts tag (`vX.Y.Z`) or branch name.
- Installer profile embedded in EXE defaults to `core`.
- EXE requires outbound access to GitHub release/source URLs.
